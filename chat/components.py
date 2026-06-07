"""Reusable FastHTML components for the 3-pane chat UI."""

from __future__ import annotations

import json

from fasthtml.common import (
    Div, Span, H2, H3, H4, P, A, Button, Form, Input, Textarea,
    Ul, Li, Script, NotStr,
)
from agents.registry import CATEGORIES, AGENTS, AGENTS_BY_SLUG
from utils.version import __version__, __version_date__
from utils.i18n import t, agent_t, category_t, LANGUAGES, js_translations


def _chat_lang_dropdown(lang: str = "en"):
    """Flag dropdown for the chat header (PEHero pattern)."""
    current = LANGUAGES.get(lang, LANGUAGES["en"])
    options = [
        Button(
            Span(info["flag"], cls="lang-dd-flag"),
            Span(info["native"], cls="lang-dd-label"),
            cls=f"lang-dd-item{' active' if code == lang else ''}",
            onclick=f"fetch('/app/config',{{method:'POST',body:new URLSearchParams({{lang:'{code}'}})}}).then(()=>location.reload())",
        )
        for code, info in LANGUAGES.items()
    ]
    return Div(
        Button(current["flag"], cls="lang-trigger", onclick="toggleLangDropdown(event)"),
        Div(*options, cls="lang-dd-menu", id="lang-dd-menu"),
        cls="lang-dropdown",
    )


def signin_overlay(lang: str = "en"):
    return Div(
        Div(
            # Tab switcher
            Div(
                Button("Sign In", id="auth-tab-login", cls="auth-tab active",
                       onclick="switchAuthTab('login')"),
                Button("Register", id="auth-tab-register", cls="auth-tab",
                       onclick="switchAuthTab('register')"),
                cls="flex border-b border-gray-200 mb-4",
            ),
            # Login form
            Div(
                P("Sign in to your Kanvas.ai account", cls="text-sm text-gray-500 mb-4"),
                A(
                    Span(NotStr('<svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4"/><path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/><path d="M3.964 10.71c-.18-.54-.282-1.117-.282-1.71s.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 000 9s.348 1.452.957 2.042l3.007-2.332z" fill="#FBBC05"/><path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/></svg>'),
                     cls="google-btn-icon"),
                    Span("Continue with Google", cls="google-btn-text"),
                    href="/auth/google",
                    cls="google-btn",
                ),
                Div(Span(cls="google-divider-line"), Span("or", cls="google-divider-text"), Span(cls="google-divider-line"), cls="google-divider"),
                Input(type="email", id="login-email", placeholder="Email",
                      cls="w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-3",
                      onkeydown="if(event.key==='Enter')document.getElementById('login-password').focus()"),
                Input(type="password", id="login-password", placeholder="Password",
                      cls="w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-2",
                      onkeydown="if(event.key==='Enter')doLogin()"),
                A("Forgot password?", href="#", onclick="showForgotPassword(event)",
                  cls="text-xs text-gray-400 hover:text-black block mb-4"),
                Div(id="login-error", cls="text-red-500 text-xs mb-2"),
                Div(
                    Button("Sign In", onclick="doLogin()",
                           cls="px-4 py-2 bg-black text-white rounded-md text-sm cursor-pointer border-none"),
                    Button("Cancel", onclick="document.getElementById('signin-overlay').classList.remove('visible')",
                           cls="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm cursor-pointer border-none ml-2"),
                    cls="flex gap-2",
                ),
                id="auth-form-login",
            ),
            # Register form
            Div(
                P("Create a Kanvas.ai account", cls="text-sm text-gray-500 mb-4"),
                Input(type="text", id="reg-name", placeholder="Name (optional)",
                      cls="w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-3"),
                Input(type="email", id="reg-email", placeholder="Email",
                      cls="w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-3"),
                Input(type="password", id="reg-password", placeholder="Password (min 6 chars)",
                      cls="w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-3",
                      onkeydown="if(event.key==='Enter')doRegister()"),
                Div(id="reg-error", cls="text-red-500 text-xs mb-2"),
                Div(id="reg-success", cls="text-green-600 text-xs mb-2"),
                Div(
                    Button("Register", onclick="doRegister()",
                           cls="px-4 py-2 bg-black text-white rounded-md text-sm cursor-pointer border-none"),
                    Button("Cancel", onclick="document.getElementById('signin-overlay').classList.remove('visible')",
                           cls="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm cursor-pointer border-none ml-2"),
                    cls="flex gap-2",
                ),
                id="auth-form-register",
                style="display:none",
            ),
            # Forgot password form
            Div(
                P("Enter your email to receive a reset link", cls="text-sm text-gray-500 mb-4"),
                Input(type="email", id="forgot-email", placeholder="Email",
                      cls="w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-3",
                      onkeydown="if(event.key==='Enter')doForgot()"),
                Div(id="forgot-msg", cls="text-sm mb-2"),
                Div(
                    Button("Send Reset Link", onclick="doForgot()",
                           cls="px-4 py-2 bg-black text-white rounded-md text-sm cursor-pointer border-none"),
                    A("Back to login", href="#", onclick="switchAuthTab('login');return false",
                      cls="text-sm text-gray-500 ml-3"),
                    cls="flex items-center gap-2",
                ),
                id="auth-form-forgot",
                style="display:none",
            ),
            cls="bg-white rounded-lg p-6 shadow-xl max-w-sm w-full",
        ),
        id="signin-overlay",
        cls="signin-overlay",
    )


def left_pane(user_email=None, sessions=None, current_sid="", lang: str = "en"):
    sessions = sessions or []

    session_items = []
    for s in sessions[:30]:
        sid = str(s.get("id", ""))
        title = (s.get("title") or "New chat")[:40]
        active_cls = " active" if sid == current_sid else ""
        session_items.append(
            Div(
                A(title, href=f"/app?sid={sid}", cls="session-title"),
                Button(
                    NotStr('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>'),
                    cls="session-share-btn",
                    onclick=f"shareSession('{sid}',event)",
                    title="Copy share link",
                ),
                cls=f"session-item{active_cls}",
            )
        )

    agent_groups = []
    for cat in CATEGORIES:
        cat_agents = [a for a in AGENTS if a.category == cat["key"]]
        items = []
        for a in cat_agents:
            items.append(
                Button(
                    Span(a.icon, cls="agent-icon"),
                    Span(a.name, cls="agent-name"),
                    cls="agent-item",
                    onclick=f"agentClick('{a.prefix} ')",
                )
            )
        group_id = f"group-{cat['key']}"
        agent_groups.append(Div(
            Button(
                Span(cat["icon"], cls="cat-icon"),
                Span(cat["name"], cls="cat-name"),
                id=f"btn-{group_id}",
                cls="cat-header",
                onclick=f"toggleGroup('{group_id}')",
            ),
            Div(*items, id=group_id, cls="cat-agents"),
        ))

    auth_section = (
        Div(
            Div(
                Span(user_email, cls="text-xs text-gray-500 truncate"),
                Div(
                    A("Preferences", href="/app/profile", cls="text-xs text-gray-400 hover:text-black no-underline"),
                    Button(t("chat_sign_out", lang), onclick="signOut()", cls="text-xs text-gray-400 hover:text-black cursor-pointer bg-transparent border-none"),
                    cls="flex gap-3",
                ),
            ),
            cls="flex items-center justify-between gap-2 px-3 py-2",
        ) if user_email else
        Button(t("chat_sign_in", lang), onclick="showSignIn()",
               cls="w-full text-sm py-2 bg-black text-white rounded-md cursor-pointer border-none")
    )

    return Div(
        Div(
            A("Kanvas", Span(".ai", cls="opacity-50"), href="/",
              cls="font-display text-lg font-bold text-black no-underline tracking-tight block mb-2"),
            Button(t("chat_new", lang), onclick="newChat()",
                   cls="new-chat-btn"),
            cls="px-3 pt-3",
        ),
        Div(
            H4(t("chat_history", lang), cls="section-label"),
            Div(*session_items, cls="session-list") if session_items else
            P(t("chat_no_sessions", lang), cls="text-xs text-gray-400 px-3"),
            cls="history-section",
        ),
        Div(
            H4(t("chat_agents", lang), cls="section-label"),
            *agent_groups,
            cls="agents-section",
        ),
        Div(
            A("Art Index", href="/app/market-map", cls="workspace-link"),
            A("Analytics", href="/app/analytics", cls="workspace-link"),
            A("\U0001f3ae Art Guru", href="/app/art-guru", cls="workspace-link"),
            cls="workspace-section",
        ),
        Div(auth_section, cls="auth-section"),
        Div(
            Span(f"v{__version__}", cls="text-[10px] text-gray-300"),
            Span(f"{__version_date__}", cls="text-[10px] text-gray-300"),
            cls="flex items-center justify-between px-3 py-2 border-t border-gray-100",
        ),
        cls="left-pane",
    )


def center_pane(messages=None, current_agent_slug=None, lang: str = "en"):
    messages = messages or []
    agent_names_json = json.dumps({a.slug: a.name for a in AGENTS})
    agent_prompts_json = json.dumps({a.slug: list(a.example_prompts) for a in AGENTS})

    msg_els = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        agent = m.get("agent_slug")
        bubble = Div(content, cls="msg-bubble")
        if role == "assistant" and agent:
            spec = AGENTS_BY_SLUG.get(agent)
            agent_label = Div(
                Span(spec.icon if spec else "*", cls="msg-agent-icon"),
                Span(spec.name if spec else agent, cls="msg-agent-label"),
                cls="msg-agent",
            )
            msg_els.append(Div(agent_label, bubble, cls=f"msg msg-{role}"))
        else:
            msg_els.append(Div(bubble, cls=f"msg msg-{role}"))

    current_agent = AGENTS_BY_SLUG.get(current_agent_slug)
    is_game = current_agent_slug == "art_guru"

    if is_game:
        welcome_title = "\U0001f3ae Art Guru"
        welcome_body = "An AI-powered art collection RPG. Choose your character and enter the art world."
        header_title = "\U0001f3ae Art Guru"
    else:
        welcome_title = t("chat_welcome_title", lang)
        welcome_body = t("chat_welcome_body", lang)
        header_title = current_agent.name if current_agent else "Art Advisor"

    welcome = Div(
        H2(welcome_title, cls="text-2xl font-display font-bold mb-2"),
        P(welcome_body, cls="text-sm text-gray-500 mb-6"),
        Div(id="sample-cards-row", cls="sample-cards-row"),
        Div(id="sample-cards-label", cls="sample-cards-label-wrap"),
        id="welcome-hero",
        cls="welcome-hero",
        style="" if not messages else "display:none",
    )

    return Div(
        Div(
            Div(
                Button("=", cls="mobile-menu-btn", onclick="toggleLeftPane()"),
                Span(header_title, id="current-agent-label", cls="chat-header-title"),
                cls="chat-header-left",
            ),
            Div(
                _chat_lang_dropdown(lang),
                Button(
                    NotStr('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg>'),
                    Span(t("chat_copy", lang), cls="btn-label"),
                    id="copy-chat-btn", onclick="copyChat()", cls="header-action-btn copy-btn", title="Copy chat",
                ),
                Button(
                    NotStr('<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>'),
                    Span("Share", cls="btn-label"),
                    id="share-btn", onclick="shareChat()", cls="header-action-btn share-btn", title="Share link",
                ),
                Button(t("chat_canvas", lang), id="artifact-btn", onclick="toggleArtifactPane()", cls="header-action-btn canvas-btn"),
                Button("\U0001f4f0", id="news-toggle-btn", onclick="toggleArtifactPane()", cls="header-action-btn news-toggle-btn",
                       title="Art News"),
                cls="chat-header-actions",
            ),
            cls="chat-header",
        ),
        Div(
            welcome,
            *msg_els,
            id="messages",
            cls="messages",
        ),
        Form(
            Textarea(
                id="chat-input", name="msg", rows="1",
                placeholder=t("chat_placeholder", lang),
                onkeydown="handleKey(event)", oninput="autoResize(this); onInputChange(this)",
            ),
            Button("->", id="send-btn", type="button", onclick="sendMessage(event)",
                   cls="send-btn"),
            cls="chat-form",
        ),
        Script(NotStr(f'document.getElementById("agent-prompts-data").textContent = {json.dumps(agent_prompts_json)};'), type="text/javascript") if False else "",
        Script(json.dumps({a.slug: list(a.example_prompts) for a in AGENTS}),
               id="agent-prompts-data", type="application/json"),
        Script(json.dumps({a.slug: a.name for a in AGENTS}),
               id="agent-names-data", type="application/json"),
        cls="center-pane",
    )


def right_pane(lang: str = "en"):
    return Div(
        Div(
            Div(
                H4(t("chat_news_title", lang), cls="artifact-title"),
                Span(t("chat_news_subtitle", lang), id="artifact-subtitle", cls="artifact-subtitle"),
            ),
            Button("✕", cls="right-close", onclick="toggleArtifactPane()"),
            cls="artifact-header",
        ),
        Div(
            P(t("js_loading_news", lang), cls="text-sm text-gray-400"),
            id="artifact-empty",
            cls="px-4 py-2 overflow-y-auto flex-1",
        ),
        Div(id="artifact-body", cls="artifact-body", style="display:none"),
        id="right-pane",
        cls="right-pane open",
    )
