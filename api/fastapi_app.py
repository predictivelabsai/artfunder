"""FastAPI application for the Kanvas API.

Standalone API server for api.kanvas.ai — art advisory platform with 8 specialist agents.
Also mountable in main.py at /api/v1 for dual deploy.
"""

from __future__ import annotations

import json
import logging
import secrets

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.fastapi_auth import create_token
from api.fastapi_schemas import (
    LoginRequest, RegisterRequest, AuthResponse, UserInfo,
    ChatRequest, SessionSummary, SessionDetail, MessageOut, ShareResponse, SharedSessionOut,
    AgentOut,
    UserProfileOut, UpdateProfileRequest,
    ContactRequest,
)
from api.fastapi_deps import get_db, get_current_user, get_optional_user
from auth.utils import hash_password, verify_password

log = logging.getLogger(__name__)

SCHEMA = "kanvas"


def _json_list(val) -> list:
    if not val:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        return json.loads(val)
    return []


def create_app(root_path: str = "") -> FastAPI:
    """Build the FastAPI app. Routes have no prefix — that comes from the mount point or reverse proxy."""
    api = FastAPI(
        title="Kanvas API",
        description="API for Kanvas.ai — AI art advisory platform for the Baltic & Nordic art market",
        version="1.0.0",
        root_path=root_path,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Health ────────────────────────────────────────────────────────

    @api.get("/health", tags=["health"])
    def health():
        return {"status": "ok"}

    # ── Auth ──────────────────────────────────────────────────────────

    @api.post("/auth/register", response_model=AuthResponse, tags=["auth"])
    def register(body: RegisterRequest, db: Session = Depends(get_db)):
        existing = db.execute(
            text(f"SELECT id, password_hash FROM {SCHEMA}.chat_users WHERE email = :email"),
            {"email": body.email},
        ).fetchone()

        if existing and existing.password_hash:
            raise HTTPException(409, "An account with this email already exists")

        pw_hash = hash_password(body.password)

        if existing:
            db.execute(
                text(f"UPDATE {SCHEMA}.chat_users SET password_hash = :pw, name = :name, is_verified = TRUE WHERE email = :email"),
                {"pw": pw_hash, "name": body.name, "email": body.email},
            )
            db.commit()
            uid = existing.id
        else:
            row = db.execute(
                text(f"INSERT INTO {SCHEMA}.chat_users (email, password_hash, name, is_verified) "
                     "VALUES (:email, :pw, :name, TRUE) RETURNING id"),
                {"email": body.email, "pw": pw_hash, "name": body.name},
            ).fetchone()
            db.commit()
            uid = row[0]

        token = create_token(uid, body.email)
        return AuthResponse(token=token, email=body.email, name=body.name, user_id=uid)

    @api.post("/auth/login", response_model=AuthResponse, tags=["auth"])
    def login(body: LoginRequest, db: Session = Depends(get_db)):
        row = db.execute(
            text(f"SELECT id, email, password_hash, name FROM {SCHEMA}.chat_users WHERE email = :email"),
            {"email": body.email},
        ).fetchone()

        if not row or not row.password_hash:
            raise HTTPException(401, "Invalid email or password")
        if not verify_password(body.password, row.password_hash):
            raise HTTPException(401, "Invalid email or password")

        token = create_token(row.id, row.email)
        return AuthResponse(token=token, email=row.email, name=row.name or "", user_id=row.id)

    @api.post("/auth/google", response_model=AuthResponse, tags=["auth"])
    def google_auth(body: dict, db: Session = Depends(get_db)):
        """Validate a Google ID token from mobile app and return a JWT."""
        import urllib.request
        id_token = body.get("id_token")
        if not id_token:
            raise HTTPException(400, "id_token is required")

        try:
            url = f"https://oauth2.googleapis.com/tokeninfo?id_token={id_token}"
            with urllib.request.urlopen(url, timeout=10) as resp:
                info = json.loads(resp.read())
        except Exception as e:
            raise HTTPException(401, f"Invalid Google token: {e}")

        email = info.get("email")
        if not email or info.get("email_verified") != "true":
            raise HTTPException(401, "Email not verified")

        name = info.get("name", "")

        row = db.execute(
            text(f"SELECT id, name FROM {SCHEMA}.chat_users WHERE email = :email"),
            {"email": email},
        ).fetchone()

        if row:
            uid = row.id
            name = row.name or name
        else:
            r = db.execute(
                text(f"INSERT INTO {SCHEMA}.chat_users (email, name, is_verified) "
                     "VALUES (:email, :name, TRUE) RETURNING id"),
                {"email": email, "name": name},
            ).fetchone()
            db.commit()
            uid = r[0]

        token = create_token(uid, email)
        return AuthResponse(token=token, email=email, name=name, user_id=uid)

    @api.get("/auth/me", response_model=UserInfo, tags=["auth"])
    def me(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        row = db.execute(
            text(f"SELECT id, email, name FROM {SCHEMA}.chat_users WHERE id = :id"),
            {"id": user["user_id"]},
        ).fetchone()
        if not row:
            raise HTTPException(404, "User not found")
        return UserInfo(user_id=row.id, email=row.email, name=row.name or "")

    # ── Agents ────────────────────────────────────────────────────────

    @api.get("/agents", response_model=list[AgentOut], tags=["agents"])
    def list_agents():
        from agents.registry import AGENTS
        return [
            AgentOut(
                slug=a.slug, name=a.name, category=a.category,
                icon=a.icon, one_liner=a.one_liner,
                description=a.description,
                example_prompts=list(a.example_prompts),
            )
            for a in AGENTS
        ]

    # ── Sessions ──────────────────────────────────────────────────────

    @api.get("/sessions", response_model=list[SessionSummary], tags=["sessions"])
    def list_sessions(
        limit: int = 50,
        user: dict | None = Depends(get_optional_user),
        db: Session = Depends(get_db),
    ):
        uid = user["sub"] if user else 0
        rows = db.execute(
            text(f"SELECT id, title, agent_slug, updated_at FROM {SCHEMA}.chat_sessions "
                 "WHERE user_id = :uid ORDER BY updated_at DESC LIMIT :lim"),
            {"uid": uid, "lim": limit},
        ).fetchall()
        return [
            SessionSummary(id=r.id, title=r.title, agent_slug=r.agent_slug,
                           updated_at=str(r.updated_at))
            for r in rows
        ]

    @api.get("/sessions/{session_id}", response_model=SessionDetail, tags=["sessions"])
    def get_session(
        session_id: int,
        user: dict | None = Depends(get_optional_user),
        db: Session = Depends(get_db),
    ):
        uid = user["sub"] if user else 0
        row = db.execute(
            text(f"SELECT id, title, agent_slug FROM {SCHEMA}.chat_sessions WHERE id = :sid AND user_id = :uid"),
            {"sid": session_id, "uid": uid},
        ).fetchone()
        if not row:
            raise HTTPException(404, "Session not found")

        msgs = db.execute(
            text(f"SELECT role, content, agent_slug FROM {SCHEMA}.chat_messages "
                 "WHERE session_id = :sid ORDER BY id ASC"),
            {"sid": session_id},
        ).fetchall()
        return SessionDetail(
            id=row.id, title=row.title, agent_slug=row.agent_slug,
            messages=[MessageOut(role=m.role, content=m.content, agent_slug=m.agent_slug) for m in msgs],
        )

    @api.delete("/sessions/{session_id}", tags=["sessions"])
    def delete_session(
        session_id: int,
        user: dict | None = Depends(get_optional_user),
        db: Session = Depends(get_db),
    ):
        uid = user["sub"] if user else 0
        row = db.execute(
            text(f"SELECT id FROM {SCHEMA}.chat_sessions WHERE id = :sid AND user_id = :uid"),
            {"sid": session_id, "uid": uid},
        ).fetchone()
        if not row:
            raise HTTPException(404, "Session not found")

        db.execute(text(f"DELETE FROM {SCHEMA}.chat_messages WHERE session_id = :sid"), {"sid": session_id})
        db.execute(text(f"DELETE FROM {SCHEMA}.chat_sessions WHERE id = :sid"), {"sid": session_id})
        db.commit()
        return {"ok": True}

    @api.post("/sessions/{session_id}/share", response_model=ShareResponse, tags=["sessions"])
    def share_session(
        session_id: int,
        user: dict | None = Depends(get_optional_user),
        db: Session = Depends(get_db),
    ):
        uid = user["sub"] if user else 0
        row = db.execute(
            text(f"SELECT share_token FROM {SCHEMA}.chat_sessions WHERE id = :sid AND user_id = :uid"),
            {"sid": session_id, "uid": uid},
        ).fetchone()
        if not row:
            raise HTTPException(404, "Session not found")

        token = row.share_token
        if not token:
            token = secrets.token_urlsafe(32)
            db.execute(
                text(f"UPDATE {SCHEMA}.chat_sessions SET share_token = :token WHERE id = :sid"),
                {"token": token, "sid": session_id},
            )
            db.commit()
        return ShareResponse(token=token, url=f"/shared/{token}")

    @api.get("/shared/{token}", response_model=SharedSessionOut, tags=["sessions"])
    def get_shared_session(token: str, db: Session = Depends(get_db)):
        row = db.execute(
            text(f"SELECT s.id, s.title, s.agent_slug "
                 f"FROM {SCHEMA}.chat_sessions s "
                 f"WHERE s.share_token = :token"),
            {"token": token},
        ).fetchone()
        if not row:
            raise HTTPException(404, "Shared session not found")
        msgs = db.execute(
            text(f"SELECT role, content, agent_slug FROM {SCHEMA}.chat_messages "
                 "WHERE session_id = :sid ORDER BY id ASC"),
            {"sid": row[0]},
        ).fetchall()
        return SharedSessionOut(
            title=row[1] or "Shared Chat",
            agent_slug=row[2],
            messages=[MessageOut(role=m.role, content=m.content, agent_slug=m.agent_slug) for m in msgs],
        )

    # ── Chat (SSE streaming) ─────────────────────────────────────────

    @api.post("/chat", tags=["chat"],
              responses={200: {"content": {"text/event-stream": {}},
                               "description": "SSE stream of chat events"}})
    def chat(
        body: ChatRequest,
        user: dict | None = Depends(get_optional_user),
        db: Session = Depends(get_db),
    ):
        # Anonymous requests (no valid token) have no chat_users row, so store
        # their sessions with user_id = NULL — the FK to chat_users allows NULL,
        # whereas user_id = 0 violates it and 500s. `IS NOT DISTINCT FROM` lets
        # NULL match NULL on lookup so anonymous follow-ups reuse their session.
        owner_id = user["sub"] if user else None

        if body.session_id:
            row = db.execute(
                text(f"SELECT id FROM {SCHEMA}.chat_sessions "
                     "WHERE id = :sid AND user_id IS NOT DISTINCT FROM :uid"),
                {"sid": body.session_id, "uid": owner_id},
            ).fetchone()
            session_id = row.id if row else None
        else:
            session_id = None

        if not session_id:
            row = db.execute(
                text(f"INSERT INTO {SCHEMA}.chat_sessions (user_id, title) VALUES (:uid, :title) RETURNING id"),
                {"uid": owner_id, "title": body.message[:80]},
            ).fetchone()
            db.commit()
            session_id = row[0]

        from agents import router as agent_router
        from agents.registry import by_slug
        agent_slug = agent_router.route(body.message)
        spec = by_slug(agent_slug)

        db.execute(
            text(f"INSERT INTO {SCHEMA}.chat_messages (session_id, role, content) VALUES (:sid, 'user', :content)"),
            {"sid": session_id, "content": body.message},
        )
        db.commit()

        history_rows = db.execute(
            text(f"SELECT role, content FROM {SCHEMA}.chat_messages "
                 "WHERE session_id = :sid ORDER BY id ASC"),
            {"sid": session_id},
        ).fetchall()
        history = [{"role": r.role, "content": r.content} for r in history_rows[:-1]]

        stripped_msg = agent_router.strip_prefix(body.message)

        async def event_stream():
            from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
            from utils.i18n import LANGUAGES

            yield _sse_event("session", {"sid": session_id})
            yield _sse_event("agent_route", {
                "slug": agent_slug,
                "agent": spec.name if spec else agent_slug,
                "icon": spec.icon if spec else "~",
            })

            lang_info = LANGUAGES.get(body.lang, LANGUAGES["en"])
            lang_directive = ""
            if body.lang != "en":
                lang_directive = f"\nUser language: {body.lang} ({lang_info['name']}). Respond in {lang_info['name']}."

            lc_messages = [SystemMessage(content=f"You are a Kanvas art advisor. Respond helpfully and concisely.{lang_directive}")]
            for h in history[-20:]:
                if h["role"] == "user":
                    lc_messages.append(HumanMessage(content=h["content"]))
                elif h["role"] == "assistant":
                    lc_messages.append(AIMessage(content=h["content"]))
            lc_messages.append(HumanMessage(content=stripped_msg))

            accumulated = []
            tool_calls_log = []

            try:
                from agents.base import cached_agent
                graph = cached_agent(agent_slug)

                async for ev in graph.astream_events({"messages": lc_messages}, version="v2"):
                    kind = ev["event"]
                    if kind == "on_chat_model_stream":
                        chunk = ev["data"].get("chunk")
                        if chunk and hasattr(chunk, "content") and isinstance(chunk.content, str) and chunk.content:
                            if not getattr(chunk, "tool_call_chunks", None):
                                accumulated.append(chunk.content)
                                yield _sse_event("token", {"text": chunk.content})
                    elif kind == "on_chat_model_end":
                        # If this model turn requested tool calls, any text it
                        # streamed was intermediate reasoning (frequently raw
                        # SQL). Drop it server-side and tell the client to clear
                        # its streamed buffer so only the final answer remains.
                        msg = ev["data"].get("output")
                        tool_calls = getattr(msg, "tool_calls", None)
                        if not tool_calls and isinstance(msg, dict):
                            tool_calls = msg.get("tool_calls")
                        if tool_calls:
                            accumulated.clear()
                            yield _sse_event("reset", {})
                    elif kind == "on_tool_start":
                        name = ev.get("name", "unknown")
                        args = ev["data"].get("input", {})
                        tool_calls_log.append({"name": name, "args": args})
                        yield _sse_event("tool_start", {"name": name, "args": args})
                    elif kind == "on_tool_end":
                        name = ev.get("name", "unknown")
                        raw = ev["data"].get("output", "")
                        output = getattr(raw, "content", None) or (raw if isinstance(raw, str) else str(raw))

                        # A tool may embed a chart payload as `...prose...__ARTIFACT__{json}`.
                        # Emit the chart as a structured artifact_show event and strip the
                        # raw JSON (and any leading SQL/marker) from the human-visible
                        # tool output so it never renders as a wall of SQL/JSON in chat.
                        clean = output
                        if isinstance(output, str) and "__ARTIFACT__" in output:
                            marker = output.index("__ARTIFACT__")
                            artifact_str = output[marker + len("__ARTIFACT__"):]
                            sep = artifact_str.find("\n\n")
                            if sep != -1:
                                artifact_str = artifact_str[:sep]
                            try:
                                payload = json.loads(artifact_str)
                                yield _sse_event("artifact_show", payload)
                            except Exception:
                                pass
                            clean = output[:marker].rstrip()

                        yield _sse_event("tool_end", {"name": name, "output": clean[:2000]})
            except Exception as e:
                log.exception("chat stream failed")
                yield _sse_event("error", {"message": str(e)})

            final = "".join(accumulated) or "(no response)"

            from db import SessionLocal
            persist_db = SessionLocal()
            try:
                persist_db.execute(
                    text(f"INSERT INTO {SCHEMA}.chat_messages (session_id, role, content, agent_slug, tool_calls) "
                         "VALUES (:sid, 'assistant', :content, :agent, :tools)"),
                    {"sid": session_id, "content": final, "agent": agent_slug,
                     "tools": json.dumps(tool_calls_log) if tool_calls_log else None},
                )
                persist_db.execute(
                    text(f"UPDATE {SCHEMA}.chat_sessions SET agent_slug = :slug, updated_at = now() WHERE id = :sid"),
                    {"slug": agent_slug, "sid": session_id},
                )
                persist_db.commit()
            finally:
                persist_db.close()

            yield _sse_event("done", {"slug": agent_slug, "tools": len(tool_calls_log)})

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    # ── Profile ──────────────────────────────────────────────────────

    @api.get("/profile", response_model=UserProfileOut, tags=["profile"])
    def get_profile(user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        u = db.execute(
            text(f"SELECT name, email FROM {SCHEMA}.chat_users WHERE id = :id"),
            {"id": user["user_id"]},
        ).fetchone()
        if not u:
            raise HTTPException(404, "User not found")

        prefs = db.execute(
            text(f"SELECT * FROM {SCHEMA}.user_profiles WHERE user_id = :uid"),
            {"uid": user["user_id"]},
        ).fetchone()

        p = dict(prefs._mapping) if prefs else {}
        return UserProfileOut(
            name=u.name or "",
            email=u.email,
            phone=p.get("phone") or "",
            country=p.get("country") or "",
            city=p.get("city") or "",
            currency=p.get("currency") or "EUR",
            language=p.get("language") or "en",
            budget_min_eur=float(p["budget_min_eur"]) if p.get("budget_min_eur") else None,
            budget_max_eur=float(p["budget_max_eur"]) if p.get("budget_max_eur") else None,
            preferred_mediums=_json_list(p.get("preferred_mediums")),
            preferred_periods=_json_list(p.get("preferred_periods")),
            preferred_auction_houses=_json_list(p.get("preferred_auction_houses")),
            preferred_countries=_json_list(p.get("preferred_countries")),
            min_year=p.get("min_year"),
            max_year=p.get("max_year"),
            notify_new_results=p.get("notify_new_results", True),
            notify_price_alerts=p.get("notify_price_alerts", True),
            notify_weekly_digest=p.get("notify_weekly_digest", True),
        )

    @api.post("/profile", tags=["profile"])
    def update_profile(body: UpdateProfileRequest, user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
        uid = user["user_id"]
        if body.name is not None:
            db.execute(text(f"UPDATE {SCHEMA}.chat_users SET name = :name WHERE id = :id"),
                       {"name": body.name, "id": uid})

        existing = db.execute(
            text(f"SELECT user_id FROM {SCHEMA}.user_profiles WHERE user_id = :uid"),
            {"uid": uid},
        ).fetchone()

        fields = {}
        for field in ["phone", "country", "city", "currency", "language",
                      "budget_min_eur", "budget_max_eur",
                      "min_year", "max_year",
                      "notify_new_results", "notify_price_alerts", "notify_weekly_digest"]:
            val = getattr(body, field, None)
            if val is not None:
                fields[field] = val

        for field in ["preferred_mediums", "preferred_periods",
                      "preferred_auction_houses", "preferred_countries"]:
            val = getattr(body, field, None)
            if val is not None:
                fields[field] = json.dumps(val)

        if existing:
            if fields:
                set_clause = ", ".join(f"{k} = :{k}" for k in fields)
                db.execute(text(f"UPDATE {SCHEMA}.user_profiles SET {set_clause}, updated_at = NOW() WHERE user_id = :uid"),
                           {**fields, "uid": uid})
        else:
            fields["user_id"] = uid
            cols = ", ".join(fields.keys())
            vals = ", ".join(f":{k}" for k in fields)
            db.execute(text(f"INSERT INTO {SCHEMA}.user_profiles ({cols}) VALUES ({vals})"), fields)

        db.commit()
        return {"ok": True}

    # ── Contact ──────────────────────────────────────────────────────

    @api.post("/contact", tags=["contact"])
    def submit_contact(body: ContactRequest):
        log.info("Contact form: name=%s email=%s message=%s", body.name, body.email, body.message[:200])
        return {"ok": True, "message": "Thank you for your message. We will get back to you soon."}

    return api


def _sse_event(name: str, data: dict) -> str:
    return f"event: {name}\ndata: {json.dumps(data, default=str)}\n\n"


api_app = create_app()


if __name__ == "__main__":
    import uvicorn
    standalone = create_app()
    uvicorn.run(standalone, host="0.0.0.0", port=5012)
