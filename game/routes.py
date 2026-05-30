"""Art Guru game routes — text RPG at /app/art-guru."""

from __future__ import annotations

import json
import logging

from langchain_core.messages import HumanMessage, SystemMessage
from starlette.requests import Request
from starlette.responses import StreamingResponse, JSONResponse

from chat.layout import chat_page
from chat import sse
from game.engine import (
    CHARACTERS, GameState, new_game, draw_event, format_status,
    STAGES, ROUNDS_TOTAL,
)
from game.prompts import GAME_MASTER_SYSTEM, SERAH_INTRO, CHARACTER_SELECT

log = logging.getLogger(__name__)

CHAR_MAP = {
    "1": "famous_artist", "famous artist": "famous_artist",
    "2": "emerging_artist", "emerging artist": "emerging_artist",
    "3": "gallerist", "gallerist": "gallerist",
    "4": "museum_curator", "museum curator": "museum_curator",
    "5": "billionaire_collector", "billionaire collector": "billionaire_collector",
    "6": "regular_collector", "regular collector": "regular_collector",
}


def _get_game_state(sess) -> GameState | None:
    raw = sess.get("art_guru_state")
    if raw:
        try:
            return GameState.from_dict(json.loads(raw) if isinstance(raw, str) else raw)
        except Exception:
            pass
    return None


def _save_game_state(sess, state: GameState):
    sess["art_guru_state"] = json.dumps(state.to_dict())


def _build_system_prompt(state: GameState) -> str:
    char = CHARACTERS.get(state.character, {})
    event = draw_event()
    state.events_history.append(event["name"])

    char_info = (
        f"**{char['name']}** ({char['icon']})\n"
        f"Ability: {char['ability']}\n"
        f"Background: {char['description']}"
    )

    return GAME_MASTER_SYSTEM.format(
        total_rounds=state.total_rounds,
        status=format_status(state),
        event=f"**{event['name']}**: {event['effect']}",
        character_info=char_info,
        serah_trust=state.serah_trust,
    )


def register_game_routes(rt):
    """Register Art Guru game routes."""

    @rt("/app/art-guru")
    def art_guru_home(sess):
        from utils.i18n import get_lang
        lang = get_lang(sess)
        return chat_page(
            user_email=sess.get("email"),
            sessions=[],
            current_sid="art-guru",
            messages=[],
            current_agent_slug="art_guru",
            lang=lang,
        )

    @rt("/app/art-guru/chat", methods=["POST"])
    async def art_guru_chat(request: Request):
        sess = request.session
        form = await request.form()
        user_msg = (form.get("msg") or "").strip()

        if not user_msg:
            return JSONResponse({"error": "empty message"}, status_code=400)

        state = _get_game_state(sess)

        async def event_stream():
            nonlocal state

            yield sse.event("session", {"sid": "art-guru"})
            yield sse.event(sse.AGENT_ROUTE, {
                "slug": "art_guru",
                "agent": "Art Guru",
                "icon": "\U0001f3ae",
            })

            # Character selection phase
            if state is None:
                choice = user_msg.lower().strip().rstrip(".")
                char_key = CHAR_MAP.get(choice)

                if not char_key:
                    yield sse.event(sse.TOKEN, {"text": CHARACTER_SELECT})
                    yield sse.event(sse.DONE, {"slug": "art_guru"})
                    return

                state = new_game(char_key, player_name=sess.get("email", "Art Guru"))
                _save_game_state(sess, state)

                # Send intro + Serah Vale + first round
                char = CHARACTERS[char_key]
                intro = (
                    f"# You are the {char['icon']} {char['name']}\n\n"
                    f"*{char['description']}*\n\n"
                    f"**Starting resources:** {char['start_gold']:,} gold | {char['start_knowledge']} knowledge\n"
                    f"**Special ability:** {char['ability']}\n\n"
                    f"---\n\n"
                    f"{SERAH_INTRO}\n\n"
                    f"---\n\n"
                    f"## Round 1 begins...\n\n"
                )
                yield sse.event(sse.TOKEN, {"text": intro})

                # Now run the first game master turn
                system = _build_system_prompt(state)
                await _run_game_turn(
                    system, state, sess,
                    "I just chose my character and the game is starting. Present Round 1, Stage 1: Creation & Acquisition. Introduce the art market setting and give me my first choices.",
                    event_stream_yield=lambda e: None,
                    token_collector=[],
                )
                # Re-stream with actual LLM
                system = _build_system_prompt(state)
                accumulated = []
                try:
                    from utils.llm import build_llm
                    llm = build_llm()
                    messages = [
                        SystemMessage(content=system),
                        HumanMessage(content="The game begins! Present Round 1, Stage 1: Creation & Acquisition. Set the scene in the Estonian art world. Show available artworks with prices from real Estonian artists. Give me 3-4 choices."),
                    ]
                    for chunk in llm.stream(messages):
                        if hasattr(chunk, "content") and chunk.content:
                            accumulated.append(chunk.content)
                            yield sse.event(sse.TOKEN, {"text": chunk.content})
                except Exception as e:
                    log.exception("Game master LLM failed")
                    yield sse.event(sse.ERROR, {"message": str(e)})

                _save_game_state(sess, state)
                yield sse.event(sse.DONE, {"slug": "art_guru"})
                return

            # Game over check
            if state.game_over:
                yield sse.event(sse.TOKEN, {"text": "The game has ended! Type **new game** to start over."})
                if "new game" in user_msg.lower():
                    sess.pop("art_guru_state", None)
                    yield sse.event(sse.TOKEN, {"text": "\n\n" + CHARACTER_SELECT})
                yield sse.event(sse.DONE, {"slug": "art_guru"})
                return

            # Normal game turn — send to LLM game master
            system = _build_system_prompt(state)

            # Build conversation history
            messages = [
                SystemMessage(content=system),
                HumanMessage(content=f"Player action: {user_msg}\n\nProcess this action for the current stage ({state.current_stage()}). Update the game state accordingly. If the stage is complete, advance to the next stage. If all stages are done, advance to the next round. Present the results and the next set of choices."),
            ]

            accumulated = []
            try:
                from utils.llm import build_llm
                llm = build_llm()
                for chunk in llm.stream(messages):
                    if hasattr(chunk, "content") and chunk.content:
                        accumulated.append(chunk.content)
                        yield sse.event(sse.TOKEN, {"text": chunk.content})
            except Exception as e:
                log.exception("Game master LLM failed")
                yield sse.event(sse.ERROR, {"message": str(e)})

            # Advance stage/round based on game logic
            response_text = "".join(accumulated).lower()
            if any(kw in response_text for kw in ["next stage", "stage complete", "moving to", "advance to"]):
                state.stage_idx += 1
                if state.stage_idx >= len(STAGES):
                    state.stage_idx = 0
                    state.round += 1
                    if state.round > state.total_rounds:
                        state.game_over = True
                        state.score = state.collection_value() + (state.knowledge * 500) + state.gold

            # Check for Serah Vale trust building
            if "serah" in user_msg.lower() or "vale" in user_msg.lower():
                state.serah_trust = min(10, state.serah_trust + 1)

            # Check for special power usage
            if "special power" in user_msg.lower() or "ability" in user_msg.lower():
                if not state.special_power_used:
                    state.special_power_used = True

            _save_game_state(sess, state)
            yield sse.event(sse.DONE, {"slug": "art_guru"})

        return StreamingResponse(event_stream(), media_type="text/event-stream")

    @rt("/app/art-guru/reset", methods=["POST"])
    async def art_guru_reset(request: Request):
        request.session.pop("art_guru_state", None)
        return JSONResponse({"ok": True})


async def _run_game_turn(system, state, sess, prompt, event_stream_yield, token_collector):
    """Helper to run a game master turn (used internally)."""
    pass
