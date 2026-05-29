"""Reusable FastHTML components for the 3-pane chat UI."""

from __future__ import annotations

import json

from fasthtml.common import (
    Div, Span, H2, H3, H4, P, A, Button, Form, Input, Textarea,
    Ul, Li, Script, NotStr,
)
from agents.registry import CATEGORIES, AGENTS, AGENTS_BY_SLUG
from utils.version import __version__, __version_date__


def signin_overlay():
    return Div(
        Div(
            H3("Sign in to Kanvas.ai", cls="text-lg font-semibold mb-4"),
            P("Enter your email to save chat history.", cls="text-sm text-gray-500 mb-4"),
            Input(type="email", id="signin-email", placeholder="you@example.com",
                  cls="w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-3",
                  onkeydown="if(event.key==='Enter')doSignIn()"),
            Div(
                Button("Sign in", onclick="doSignIn()",
                       cls="px-4 py-2 bg-black text-white rounded-md text-sm cursor-pointer border-none"),
                Button("Cancel", onclick="document.getElementById('signin-overlay').classList.remove('visible')",
                       cls="px-4 py-2 bg-gray-100 text-gray-700 rounded-md text-sm cursor-pointer border-none ml-2"),
                cls="flex gap-2",
            ),
            cls="bg-white rounded-lg p-6 shadow-xl max-w-sm w-full",
        ),
        id="signin-overlay",
        cls="signin-overlay",
    )


def left_pane(user_email=None, sessions=None, current_sid=""):
    sessions = sessions or []

    session_items = []
    for s in sessions[:30]:
        sid = str(s.get("id", ""))
        title = (s.get("title") or "New chat")[:40]
        active_cls = " active" if sid == current_sid else ""
        session_items.append(
            A(title, href=f"/app?sid={sid}",
              cls=f"session-item{active_cls}")
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
                    onclick=f"fillChat('{a.prefix} ')",
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
            Span(user_email, cls="text-xs text-gray-500 truncate"),
            Button("Sign out", onclick="signOut()", cls="text-xs text-gray-400 hover:text-black cursor-pointer bg-transparent border-none"),
            cls="flex items-center justify-between gap-2 px-3 py-2",
        ) if user_email else
        Button("Sign in", onclick="showSignIn()",
               cls="w-full text-sm py-2 bg-black text-white rounded-md cursor-pointer border-none")
    )

    return Div(
        Div(
            Button("+ New chat", onclick="newChat()",
                   cls="new-chat-btn"),
            cls="px-3 pt-3",
        ),
        Div(
            H4("History", cls="section-label"),
            Div(*session_items, cls="session-list") if session_items else
            P("No conversations yet.", cls="text-xs text-gray-400 px-3"),
            cls="history-section",
        ),
        Div(
            H4("Agents", cls="section-label"),
            *agent_groups,
            cls="agents-section",
        ),
        Div(
            A("Market Map", href="/app/market-map", cls="workspace-link"),
            A("Analytics", href="/app/analytics", cls="workspace-link"),
            A("Art Index", href="/app/market-map", cls="workspace-link"),
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


def center_pane(messages=None, current_agent_slug=None):
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

    welcome = Div(
        H2("Kanvas.ai Art Advisor", cls="text-2xl font-display font-bold mb-2"),
        P("Ask about artists, market trends, valuations, or collection strategy.",
          cls="text-sm text-gray-500 mb-6"),
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
                Span(current_agent.name if current_agent else "Art Advisor",
                     id="current-agent-label", cls="chat-header-title"),
                cls="chat-header-left",
            ),
            Div(
                Button("Copy", id="copy-chat-btn", onclick="copyChat()", cls="header-action-btn"),
                Button("Canvas", id="artifact-btn", onclick="toggleArtifactPane()", cls="header-action-btn"),
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
                placeholder="Ask about an artist, market trends, or get advisory...",
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


def right_pane():
    from tools.news import fetch_art_news
    news_items = []
    try:
        news_items = fetch_art_news(max_items=10)
    except Exception:
        pass

    news_els = []
    for item in news_items:
        news_els.append(
            Div(
                A(item.get("title", "Untitled"), href=item.get("url", "#"), target="_blank",
                  cls="text-sm font-medium text-black no-underline hover:underline leading-snug block"),
                Div(
                    Span(item.get("source", ""), cls="text-[10px] font-medium text-gray-400"),
                    Span(item.get("published", "")[:10], cls="text-[10px] text-gray-300") if item.get("published") else "",
                    cls="flex gap-2 mt-1",
                ),
                P(item.get("snippet", ""), cls="text-xs text-gray-400 mt-1 leading-relaxed line-clamp-2") if item.get("snippet") else "",
                cls="py-3 border-b border-gray-50",
            )
        )

    return Div(
        Div(
            H4("Art News", cls="artifact-title"),
            Span("Estonian & Baltic art market", id="artifact-subtitle", cls="artifact-subtitle"),
            cls="artifact-header",
        ),
        Div(
            *news_els if news_els else [P("Loading art news...", cls="text-sm text-gray-400")],
            id="artifact-empty",
            cls="px-4 py-2 overflow-y-auto flex-1",
        ),
        Div(id="artifact-body", cls="artifact-body", style="display:none"),
        id="right-pane",
        cls="right-pane open",
    )
