"""Art Guru game engine — state management and game logic."""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field, asdict
from typing import Optional

CHARACTERS = {
    "famous_artist": {
        "name": "Famous Artist",
        "icon": "\U0001f3a8",
        "ability": "Create a Masterpiece once per game that guarantees a high auction price.",
        "start_gold": 5000,
        "start_knowledge": 3,
        "description": "A celebrated painter whose name commands respect. Your works fetch top prices, but fame is fickle.",
    },
    "emerging_artist": {
        "name": "Emerging Artist",
        "icon": "\U0001f525",
        "ability": "Create multiple artworks with potential for rapid increase in value.",
        "start_gold": 3000,
        "start_knowledge": 2,
        "description": "Young, hungry, and bursting with potential. Your art is raw but collectors see something special.",
    },
    "gallerist": {
        "name": "Gallerist",
        "icon": "\U0001f3db",
        "ability": "Influence the perceived value of any artwork once per game.",
        "start_gold": 8000,
        "start_knowledge": 4,
        "description": "The tastemaker. You decide what's hot and what's not. Your gallery is the gateway to the art world.",
    },
    "museum_curator": {
        "name": "Museum Curator",
        "icon": "\U0001f3db️",
        "ability": "Organize an exhibition once per game that increases the value of selected artworks.",
        "start_gold": 4000,
        "start_knowledge": 5,
        "description": "Guardian of culture and history. Your exhibitions can make or break an artist's reputation.",
    },
    "billionaire_collector": {
        "name": "Billionaire Collector",
        "icon": "\U0001f4b0",
        "ability": "Starts with more resources and can outbid others at auctions.",
        "start_gold": 15000,
        "start_knowledge": 1,
        "description": "Money is no object. You collect for prestige, but do you truly understand what you own?",
    },
    "regular_collector": {
        "name": "Regular Collector",
        "icon": "\U0001f50d",
        "ability": "Earns bonus resources from studying art and discovering undervalued artworks.",
        "start_gold": 6000,
        "start_knowledge": 3,
        "description": "A passionate collector with a keen eye. You find value where others see nothing.",
    },
}

EVENT_CARDS = [
    {"name": "Art Market Boom", "effect": "All artwork values increase by 20%.", "modifier": 1.2},
    {"name": "Economic Recession", "effect": "All artwork values decrease by 15%.", "modifier": 0.85},
    {"name": "Discovery of Lost Masterpiece", "effect": "A previously unknown work surfaces. Special auction this round!", "modifier": 1.0},
    {"name": "Art Theft at Major Museum", "effect": "Security concerns. Insurance costs rise, but surviving works gain value.", "modifier": 1.1},
    {"name": "New Art Trend Emerges", "effect": "Contemporary works surge in value. Classical works dip slightly.", "modifier": 1.0},
    {"name": "Celebrity Endorsement", "effect": "A famous celebrity collects art publicly. Market interest spikes.", "modifier": 1.15},
    {"name": "Forgery Scandal", "effect": "Trust in the market shakes. Provenance becomes critical.", "modifier": 0.9},
    {"name": "Biennale Exhibition", "effect": "International attention on the art world. Exhibition pieces gain 25% value.", "modifier": 1.25},
    {"name": "Tax Law Change", "effect": "New tax incentives for art donations. Philanthropic collectors benefit.", "modifier": 1.05},
    {"name": "Digital Art Revolution", "effect": "NFTs and digital art gain mainstream attention. Traditional art holds steady.", "modifier": 1.0},
    {"name": "Serah Vale Appears", "effect": "The Cartographer of Forgotten Light reveals a hidden truth about your collection.", "modifier": 1.0},
    {"name": "Art Fair Season", "effect": "Major fairs in Basel, Miami, and London. Trading volume increases.", "modifier": 1.1},
]

ROUNDS_TOTAL = 7
STAGES = ["Creation & Acquisition", "Exhibition & Learning", "Auction", "Evaluation", "Trading"]


@dataclass
class Artwork:
    title: str
    artist: str
    style: str
    base_value: int
    current_value: int
    year: int = 2024
    provenance: str = ""


@dataclass
class GameState:
    character: str = ""
    character_name: str = ""
    player_name: str = "Art Guru"
    round: int = 0
    stage_idx: int = 0
    gold: int = 0
    knowledge: int = 0
    collection: list = field(default_factory=list)
    special_power_used: bool = False
    events_history: list = field(default_factory=list)
    total_rounds: int = ROUNDS_TOTAL
    game_over: bool = False
    score: int = 0
    serah_trust: int = 0

    def current_stage(self) -> str:
        if self.stage_idx < len(STAGES):
            return STAGES[self.stage_idx]
        return "End of Round"

    def collection_value(self) -> int:
        return sum(a.get("current_value", 0) if isinstance(a, dict) else a.current_value
                    for a in self.collection)

    def to_dict(self) -> dict:
        return {
            "character": self.character,
            "character_name": self.character_name,
            "player_name": self.player_name,
            "round": self.round,
            "stage_idx": self.stage_idx,
            "gold": self.gold,
            "knowledge": self.knowledge,
            "collection": self.collection,
            "special_power_used": self.special_power_used,
            "events_history": self.events_history,
            "total_rounds": self.total_rounds,
            "game_over": self.game_over,
            "score": self.score,
            "serah_trust": self.serah_trust,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "GameState":
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


def new_game(character_key: str, player_name: str = "Art Guru") -> GameState:
    char = CHARACTERS[character_key]
    return GameState(
        character=character_key,
        character_name=char["name"],
        player_name=player_name,
        round=1,
        stage_idx=0,
        gold=char["start_gold"],
        knowledge=char["start_knowledge"],
    )


def draw_event() -> dict:
    return random.choice(EVENT_CARDS)


def format_status(state: GameState) -> str:
    char = CHARACTERS.get(state.character, {})
    icon = char.get("icon", "")
    lines = [
        f"**Round {state.round}/{state.total_rounds}** | Stage: *{state.current_stage()}*",
        f"{icon} **{state.character_name}** ({state.player_name})",
        f"Gold: {state.gold:,} | Knowledge: {state.knowledge} | Collection: {len(state.collection)} works ({state.collection_value():,} value)",
    ]
    if state.special_power_used:
        lines.append("Special power: *used*")
    else:
        lines.append(f"Special power: *available* ({char.get('ability', '')})")
    return "\n".join(lines)
