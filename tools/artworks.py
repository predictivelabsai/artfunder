"""Artwork database query tools using existing SQLAlchemy models."""

from __future__ import annotations

import json
import logging
from typing import Optional

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)


class SearchArtworksArgs(BaseModel):
    query: str = Field(default="", description="Search term for title or artist name.")
    category: Optional[str] = Field(default=None, description="Art category: painting, sculpture, photography, print, mixed_media")
    status: Optional[str] = Field(default=None, description="Status: draft, active, funded, completed")
    min_value: Optional[float] = Field(default=None, description="Minimum estimated value in EUR.")
    max_value: Optional[float] = Field(default=None, description="Maximum estimated value in EUR.")


def _search_artworks(**kw) -> str:
    args = SearchArtworksArgs(**kw)
    from db import SessionLocal
    from models import Artwork
    db = SessionLocal()
    try:
        q = db.query(Artwork)
        if args.query:
            q = q.filter(
                (Artwork.title.ilike(f"%{args.query}%")) |
                (Artwork.artist_name.ilike(f"%{args.query}%"))
            )
        if args.category:
            q = q.filter(Artwork.category == args.category)
        if args.status:
            q = q.filter(Artwork.status == args.status)
        if args.min_value is not None:
            q = q.filter(Artwork.estimated_value >= args.min_value)
        if args.max_value is not None:
            q = q.filter(Artwork.estimated_value <= args.max_value)

        results = q.limit(20).all()
        rows = []
        for a in results:
            rows.append({
                "id": a.id, "title": a.title, "artist": a.artist_name,
                "category": a.category.value if a.category else None,
                "medium": a.medium, "year": a.year_created,
                "estimated_value": float(a.estimated_value) if a.estimated_value else None,
                "status": a.status.value if a.status else None,
            })
        if not rows:
            return "No artworks found matching the criteria."

        lines = [f"Artworks ({len(rows)} results):\n"]
        for r in rows:
            val = f"EUR {r['estimated_value']:,.0f}" if r.get("estimated_value") else "N/A"
            lines.append(f"- #{r['id']} {r['title']} by {r['artist']} — {r.get('medium', '')} ({r.get('year', '')}) — {val} [{r.get('status', '')}]")
        return "\n".join(lines)
    finally:
        db.close()


class GetArtworkArgs(BaseModel):
    artwork_id: int = Field(description="The artwork ID to retrieve.")


def _get_artwork(**kw) -> str:
    args = GetArtworkArgs(**kw)
    from db import SessionLocal
    from models import Artwork
    db = SessionLocal()
    try:
        a = db.query(Artwork).get(args.artwork_id)
        if not a:
            return f"Artwork #{args.artwork_id} not found."
        return json.dumps({
            "id": a.id, "title": a.title, "description": a.description,
            "artist": a.artist_name, "category": a.category.value if a.category else None,
            "medium": a.medium, "origin_country": a.origin_country,
            "year_created": a.year_created, "dimensions": a.dimensions,
            "estimated_value": float(a.estimated_value) if a.estimated_value else None,
            "acquisition_cost": float(a.acquisition_cost) if a.acquisition_cost else None,
            "appreciation_rate": float(a.appreciation_rate) if a.appreciation_rate else None,
            "provenance": a.provenance, "image_url": a.image_url,
            "status": a.status.value if a.status else None,
        })
    finally:
        db.close()


search_artworks = StructuredTool.from_function(
    func=_search_artworks, name="search_artworks",
    description="Search the Kanvas artwork database by title, artist, category, status, or value range.",
    args_schema=SearchArtworksArgs,
)

get_artwork = StructuredTool.from_function(
    func=_get_artwork, name="get_artwork",
    description="Get full details of a specific artwork by ID.",
    args_schema=GetArtworkArgs,
)
