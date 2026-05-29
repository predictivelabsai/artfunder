"""3-pane chat page wrapper."""

from __future__ import annotations

from fasthtml.common import (
    Html, Head, Body, Meta, Title, Link, Script, NotStr,
    Div,
)

from chat.components import left_pane, center_pane, right_pane, signin_overlay


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
              messages=None, current_agent_slug=None, readonly=False):
    body = Body(
        signin_overlay(),
        Div(id="left-overlay", cls="left-overlay", onclick="toggleLeftPane()"),
        left_pane(user_email=user_email, sessions=sessions, current_sid=current_sid),
        center_pane(messages=messages, current_agent_slug=current_agent_slug),
        right_pane(),
        Script(src="/static/chat.js"),
        cls="bg-white text-ink font-sans antialiased app",
    )
    return Html(_head("Art Advisor"), body)
