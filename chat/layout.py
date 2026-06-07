"""3-pane chat page wrapper."""

from __future__ import annotations

from fasthtml.common import (
    Html, Head, Body, Meta, Title, Link, Script, NotStr,
    Div, Span, H2, P, A, Style,
)

from chat.components import left_pane, center_pane, right_pane, signin_overlay
from utils.version import __version__


TAILWIND_CONFIG = """
tailwind.config = {
  theme: {
    extend: {
      colors: {
        ink: { DEFAULT: '#1A1A1A', muted: '#6B7280', dim: '#9CA3AF' },
        surface: { DEFAULT: '#FFFFFF', alt: '#F5F5F5' },
        border: '#E5E5E5',
      },
      fontFamily: {
        display: ['Cormorant Garamond', 'Georgia', 'serif'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
}
"""


def _head(title: str = "Kanvas.ai") -> Head:
    return Head(
        Meta(charset="utf-8"),
        Meta(name="viewport", content="width=device-width, initial-scale=1"),
        Title(f"{title} -- Kanvas.ai"),
        Link(rel="icon", href="/static/favicon.ico", type="image/x-icon"),
        Link(rel="preconnect", href="https://fonts.googleapis.com"),
        Link(rel="preconnect", href="https://fonts.gstatic.com", crossorigin=""),
        Link(rel="stylesheet",
             href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Cormorant+Garamond:wght@400;500;600;700&display=swap"),
        Script(src="https://cdn.tailwindcss.com"),
        Script(NotStr(TAILWIND_CONFIG)),
        Script(src="https://cdn.plot.ly/plotly-2.35.2.min.js"),
        Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
        Link(rel="stylesheet", href="/static/app.css"),
    )


def chat_page(user_email=None, sessions=None, current_sid="",
              messages=None, current_agent_slug=None, readonly=False, lang="en"):
    from utils.config import get_news_interval
    from utils.i18n import js_translations
    import json as _json
    body = Body(
        signin_overlay(lang=lang),
        Div(id="left-overlay", cls="left-overlay", onclick="toggleLeftPane()"),
        left_pane(user_email=user_email, sessions=sessions, current_sid=current_sid, lang=lang),
        center_pane(messages=messages, current_agent_slug=current_agent_slug, lang=lang),
        right_pane(lang=lang),
        Script(str(get_news_interval()), id="news-interval", type="application/json"),
        Script(_json.dumps(js_translations(lang)), id="i18n-data", type="application/json"),
        Script(src=f"/static/chat.js?v={__version__}"),
        cls="bg-white text-ink font-sans antialiased app",
    )
    return Html(_head("Art Advisor"), body)


def shared_chat_page(messages=None, current_agent_slug=None, title=None):
    """Public read-only view of a shared chat session."""
    from agents.registry import AGENTS_BY_SLUG
    messages = messages or []

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

    agent = AGENTS_BY_SLUG.get(current_agent_slug)
    header_title = agent.name if agent else "Art Advisor"
    page_title = title or "Shared Chat"

    body = Body(
        Div(
            Div(
                Span(header_title, cls="chat-header-title"),
                A("Open Kanvas.ai", href="/app", cls="header-action-btn"),
                cls="chat-header",
                style="justify-content:space-between;",
            ),
            Div(*msg_els, id="messages", cls="messages"),
            Div(
                P("This is a shared conversation on ",
                  A("Kanvas.ai", href="/", cls="font-semibold text-black no-underline"),
                  cls="text-sm text-gray-400 text-center py-4"),
                cls="border-t border-gray-100",
            ),
            cls="center-pane",
            style="margin:0 auto; max-width:800px; height:100vh;",
        ),
        Script(src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"),
        Script(NotStr("""
            document.querySelectorAll('.msg-bubble').forEach(function(el) {
                if (el.closest('.msg-assistant')) {
                    el.innerHTML = marked.parse(el.textContent);
                }
            });
        """)),
        cls="bg-white text-ink font-sans antialiased",
    )
    return Html(_head(page_title), body)
