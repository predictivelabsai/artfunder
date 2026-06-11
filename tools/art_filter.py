"""Shared art-only filter for kanvas.auction_lots queries.

The `category` column is ~99% empty, so "is this art?" is detected from the
tech/title text: a lot counts as art UNLESS it matches the non-art word list
AND shows no fine-art medium signal — so a painting titled "Table" is kept
while a watch is dropped.

Scope: keep paintings, works on paper, prints, sculpture and art-ceramics;
drop furniture, jewelry, books, glass, clocks/watches, coins and carpets.
Patterns are Postgres POSIX regex (English / Estonian / Swedish / German terms).

Single source of truth — used by both the Art Index charts (chat.market_map)
and the text-to-SQL drafter (tools.sql_query).
"""

from __future__ import annotations

NONART_RE = (
    r"\y(furniture|mobel|mööbel|chair|stol|fatolj|fåtölj|tugitool|kapp|kummut|"
    r"cabinet|skap|skåp|byra|byrå|dresser|kommode|table|laud|bord|tisch|sofa|"
    r"soffa|sohva|diivan|desk|kirjutuslaud|shelf|riiul|bookcase|lamp|lampa|"
    r"lambi|leuchter|mirror|spegel|peegel|jewel|jewellery|jewelry|smycke|ehted|"
    r"sormus|sõrmus|brooch|brosch|prees|necklace|kaelakee|earring|korvarongas|"
    r"kõrvarõngas|orhange|örhänge|clock|klocka|watch|armbandsur|uhr|book|raamat|"
    r"bocker|böcker|bucher|bücher|coin|mynt|munt|münt|medal|medalj|munze|münze|"
    r"carpet|matta|vaip|rug|teppich|glass|glas|klaas)\y"
)

ART_MEDIUM_RE = (
    r"(oil|õli|oli|olja|olje|öl|canvas|lõuend|louend|duk|pann|watercolo|akvarell|"
    r"akvarel|aquarell|gouache|guašš|guass|tempera|pastel|acrylic|akr[uü]l|akryl|"
    r"graphic|graafika|grafi|litho|lito|etch|eau.?forte|ofort|söövitus|soovitus|"
    r"gravüür|woodcut|linocut|drypoint|mezzotint|serigraph|monotype|aquatint|"
    r"mixed media|sega.?tehnika|segatehnika|\yink\y|tušš|tuss|pencil|pliiats|"
    r"charcoal|s[uü]si|paber|\ypaper\y|panel|pann[oa]|papp|maal|painting|gemälde|"
    r"maleri|drawing|joonistus|sketch|sculpt|skulptuur|bronze|pronks|marble|"
    r"marmor|terracotta|terrakota|porcelain|portselan|ceramic|keraamika|fajanss|"
    r"fa[iy]ence)"
)

_FIELD = "LOWER(COALESCE(tech,'') || ' ' || COALESCE(title,''))"

# Bind-parameter form — for SQL the app builds itself (e.g. the market map).
ART_ONLY_SQL = f"({_FIELD} !~* :nonart OR {_FIELD} ~* :artmedium)"
ART_ONLY_BINDS = {"nonart": NONART_RE, "artmedium": ART_MEDIUM_RE}

# Inline-literal form — for embedding into LLM-drafted SQL. The regexes contain
# no single quotes, and Postgres standard_conforming_strings keeps backslashes
# (\y word boundaries) literal, so they are safe to wrap in single quotes.
ART_ONLY_INLINE = f"({_FIELD} !~* '{NONART_RE}' OR {_FIELD} ~* '{ART_MEDIUM_RE}')"

# Short token the text-to-SQL drafter writes; expanded deterministically after
# drafting so the model never has to reproduce the long regex by hand.
ART_ONLY_TOKEN = "{ART_ONLY}"


def expand_art_only(sql: str) -> str:
    """Replace the ART_ONLY_TOKEN placeholder with the inline art-only predicate."""
    return sql.replace(ART_ONLY_TOKEN, ART_ONLY_INLINE)
