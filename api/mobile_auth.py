"""JWT-based auth endpoints for the Kanvas mobile app.

The web app uses session cookies. Mobile needs stateless Bearer tokens.
These endpoints mirror the web auth surface but return JWTs instead of
setting session cookies.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone

import jwt
import requests as http_requests
from starlette.requests import Request
from starlette.responses import JSONResponse

from auth.utils import hash_password, verify_password, generate_token, send_verification_email

log = logging.getLogger(__name__)

JWT_SECRET = os.getenv("JWT_SECRET", os.getenv("SECRET_KEY", "kanvas-jwt-dev-2026"))
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 30

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

SCHEMA = "kanvas"


def _get_db():
    from db import SessionLocal
    return SessionLocal()


def _make_token(user_id: int, email: str, name: str = "") -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "name": name,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_mobile_user(request: Request) -> dict | None:
    """Extract user from Bearer token. Returns dict with sub, email, name or None."""
    auth_header = request.headers.get("authorization", "")
    if not auth_header.startswith("Bearer "):
        return None
    token = auth_header[7:]
    return decode_token(token)


def register_mobile_auth_routes(rt):

    @rt("/api/auth/token", methods=["POST"])
    async def api_auth_token(request: Request):
        """Email/password login → JWT."""
        from sqlalchemy import text
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)

        email = (body.get("email") or "").strip().lower()
        password = body.get("password") or ""

        if not email or not password:
            return JSONResponse({"error": "Email and password are required"}, status_code=400)

        db = _get_db()
        try:
            row = db.execute(
                text(f"SELECT id, email, password_hash, is_verified, name FROM {SCHEMA}.chat_users WHERE email = :email"),
                {"email": email},
            ).fetchone()
        finally:
            db.close()

        if not row:
            return JSONResponse({"error": "Invalid email or password"}, status_code=401)
        if not row.password_hash:
            return JSONResponse({"error": "no_password"}, status_code=401)
        if not verify_password(password, row.password_hash):
            return JSONResponse({"error": "Invalid email or password"}, status_code=401)

        token = _make_token(row.id, row.email, row.name or "")
        return JSONResponse({
            "token": token,
            "email": row.email,
            "name": row.name or "",
            "user_id": row.id,
        })

    @rt("/api/auth/register", methods=["POST"])
    async def api_auth_register(request: Request):
        """Register new user → JWT."""
        from sqlalchemy import text
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)

        email = (body.get("email") or "").strip().lower()
        password = body.get("password") or ""
        name = (body.get("name") or "").strip()

        if not email or not password:
            return JSONResponse({"error": "Email and password are required"}, status_code=400)
        if len(password) < 6:
            return JSONResponse({"error": "Password must be at least 6 characters"}, status_code=400)

        db = _get_db()
        try:
            existing = db.execute(
                text(f"SELECT id, password_hash FROM {SCHEMA}.chat_users WHERE email = :email"),
                {"email": email},
            ).fetchone()

            if existing and existing.password_hash:
                return JSONResponse({"error": "An account with this email already exists"}, status_code=409)

            verify_tok = generate_token()
            pw_hash = hash_password(password)

            if existing:
                db.execute(text(f"""
                    UPDATE {SCHEMA}.chat_users
                    SET password_hash = :pw, name = :name, verify_token = :token, is_verified = TRUE
                    WHERE email = :email
                """), {"pw": pw_hash, "name": name, "token": verify_tok, "email": email})
                uid = existing.id
            else:
                result = db.execute(text(f"""
                    INSERT INTO {SCHEMA}.chat_users (email, password_hash, name, verify_token, is_verified)
                    VALUES (:email, :pw, :name, :token, TRUE)
                    RETURNING id
                """), {"email": email, "pw": pw_hash, "name": name, "token": verify_tok})
                uid = result.fetchone()[0]
            db.commit()
        finally:
            db.close()

        send_verification_email(email, verify_tok, name)

        token = _make_token(uid, email, name)
        return JSONResponse({
            "token": token,
            "email": email,
            "name": name,
            "user_id": uid,
        })

    @rt("/api/auth/google", methods=["POST"])
    async def api_auth_google(request: Request):
        """Exchange Google ID token for a JWT."""
        from sqlalchemy import text
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)

        id_token = body.get("id_token") or ""
        if not id_token:
            return JSONResponse({"error": "id_token is required"}, status_code=400)

        resp = http_requests.get(
            f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}",
            timeout=10,
        )
        if resp.status_code != 200:
            return JSONResponse({"error": "Invalid Google token"}, status_code=401)

        info = resp.json()
        email = (info.get("email") or "").lower().strip()
        name = info.get("name") or ""

        if not email:
            return JSONResponse({"error": "Could not retrieve email from Google"}, status_code=401)

        aud = info.get("aud", "")
        if GOOGLE_CLIENT_ID and aud != GOOGLE_CLIENT_ID:
            web_client_id = os.getenv("GOOGLE_WEB_CLIENT_ID", "")
            if not web_client_id or aud != web_client_id:
                return JSONResponse({"error": "Token audience mismatch"}, status_code=401)

        db = _get_db()
        try:
            row = db.execute(
                text(f"SELECT id, email, name FROM {SCHEMA}.chat_users WHERE email = :email"),
                {"email": email},
            ).fetchone()

            if row:
                if not row.name and name:
                    db.execute(text(f"UPDATE {SCHEMA}.chat_users SET name = :name WHERE id = :id"),
                               {"name": name, "id": row.id})
                    db.commit()
                uid = row.id
                name = row.name or name
            else:
                result = db.execute(text(f"""
                    INSERT INTO {SCHEMA}.chat_users (email, name, is_verified)
                    VALUES (:email, :name, TRUE) RETURNING id
                """), {"email": email, "name": name})
                uid = result.fetchone()[0]
                db.commit()
        finally:
            db.close()

        token = _make_token(uid, email, name)
        return JSONResponse({
            "token": token,
            "email": email,
            "name": name,
            "user_id": uid,
        })

    @rt("/api/auth/me", methods=["GET"])
    async def api_auth_me(request: Request):
        """Validate Bearer token, return user info."""
        user = get_mobile_user(request)
        if not user:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        return JSONResponse({
            "email": user["email"],
            "name": user.get("name", ""),
            "user_id": user["sub"],
        })

    @rt("/api/agents", methods=["GET"])
    def api_agents():
        """Return the 8 agent specs as JSON."""
        from agents.registry import AGENTS, CATEGORIES
        agents_list = []
        for a in AGENTS:
            agents_list.append({
                "slug": a.slug,
                "name": a.name,
                "category": a.category,
                "icon": a.icon,
                "one_liner": a.one_liner,
                "description": a.description,
                "example_prompts": list(a.example_prompts),
            })
        return JSONResponse(agents_list)

    @rt("/api/sessions", methods=["GET"])
    async def api_sessions(request: Request):
        """List user's chat sessions."""
        from sqlalchemy import text
        user = get_mobile_user(request)
        if not user:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        uid = user["sub"]
        db = _get_db()
        try:
            rows = db.execute(
                text(f"SELECT id, title, agent_slug, updated_at FROM {SCHEMA}.chat_sessions "
                     "WHERE user_id = :uid ORDER BY updated_at DESC LIMIT 50"),
                {"uid": uid},
            ).fetchall()
            sessions = []
            for r in rows:
                m = dict(r._mapping)
                if m.get("updated_at"):
                    m["updated_at"] = m["updated_at"].isoformat()
                sessions.append(m)
        finally:
            db.close()

        return JSONResponse(sessions)

    @rt("/api/sessions/{sid}", methods=["DELETE"])
    async def api_session_delete(sid: int, request: Request):
        """Delete a chat session."""
        from sqlalchemy import text
        user = get_mobile_user(request)
        if not user:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        uid = user["sub"]
        db = _get_db()
        try:
            db.execute(
                text(f"DELETE FROM {SCHEMA}.chat_messages WHERE session_id = :sid "
                     "AND session_id IN (SELECT id FROM {SCHEMA}.chat_sessions WHERE user_id = :uid)"),
                {"sid": sid, "uid": uid},
            )
            db.execute(
                text(f"DELETE FROM {SCHEMA}.chat_sessions WHERE id = :sid AND user_id = :uid"),
                {"sid": sid, "uid": uid},
            )
            db.commit()
        finally:
            db.close()

        return JSONResponse({"ok": True})

    @rt("/api/profile", methods=["GET"])
    async def api_profile_get(request: Request):
        """Get user profile + preferences as JSON."""
        from sqlalchemy import text
        import json as _json
        user = get_mobile_user(request)
        if not user:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        uid = user["sub"]
        db = _get_db()
        try:
            u = db.execute(
                text(f"SELECT name, email FROM {SCHEMA}.chat_users WHERE id = :id"),
                {"id": uid},
            ).fetchone()
            prefs = db.execute(
                text(f"SELECT * FROM {SCHEMA}.user_profiles WHERE user_id = :uid"),
                {"uid": uid},
            ).fetchone()
        finally:
            db.close()

        def _as_list(val):
            if not val:
                return []
            if isinstance(val, list):
                return val
            return _json.loads(val)

        result = {
            "name": u.name or "" if u else "",
            "email": u.email if u else user["email"],
            "phone": prefs.phone if prefs else "",
            "country": prefs.country if prefs else "",
            "city": prefs.city if prefs else "",
            "currency": prefs.currency if prefs else "EUR",
            "language": prefs.language if prefs else "en",
            "preferred_mediums": _as_list(prefs.preferred_mediums) if prefs else [],
            "preferred_periods": _as_list(prefs.preferred_periods) if prefs else [],
            "notify_weekly_digest": prefs.notify_weekly_digest if prefs else False,
        }
        return JSONResponse(result)

    @rt("/api/profile", methods=["POST"])
    async def api_profile_update(request: Request):
        """Update user profile + preferences from JSON body."""
        from sqlalchemy import text
        import json as _json
        user = get_mobile_user(request)
        if not user:
            return JSONResponse({"error": "Unauthorized"}, status_code=401)

        uid = user["sub"]
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)

        db = _get_db()
        try:
            name = body.get("name")
            if name is not None:
                db.execute(
                    text(f"UPDATE {SCHEMA}.chat_users SET name = :name WHERE id = :id"),
                    {"name": name.strip(), "id": uid},
                )

            phone = body.get("phone", "")
            country = body.get("country", "")
            city = body.get("city", "")
            currency = body.get("currency", "EUR")
            language = body.get("language", "en")
            mediums = _json.dumps(body.get("preferred_mediums", []))
            periods = _json.dumps(body.get("preferred_periods", []))
            notify_digest = body.get("notify_weekly_digest", False)

            db.execute(text(f"""
                INSERT INTO {SCHEMA}.user_profiles
                    (user_id, phone, country, city, currency, language,
                     preferred_mediums, preferred_periods, notify_weekly_digest, updated_at)
                VALUES (:uid, :phone, :country, :city, :currency, :language,
                        :mediums, :periods, :notify, NOW())
                ON CONFLICT (user_id) DO UPDATE SET
                    phone = :phone, country = :country, city = :city,
                    currency = :currency, language = :language,
                    preferred_mediums = :mediums, preferred_periods = :periods,
                    notify_weekly_digest = :notify, updated_at = NOW()
            """), {
                "uid": uid, "phone": phone, "country": country, "city": city,
                "currency": currency, "language": language,
                "mediums": mediums, "periods": periods, "notify": notify_digest,
            })
            db.commit()
        finally:
            db.close()

        return JSONResponse({"ok": True})

    @rt("/api/contact", methods=["POST"])
    async def api_contact(request: Request):
        """Receive a contact form submission."""
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON"}, status_code=400)

        name = (body.get("name") or "").strip()
        email = (body.get("email") or "").strip()
        message = (body.get("message") or "").strip()

        if not email or not message:
            return JSONResponse({"error": "Email and message are required"}, status_code=400)

        log.info(f"Contact form: name={name}, email={email}, message={message[:100]}")
        return JSONResponse({"ok": True})
