"""Central registry of all specialist art advisory agents."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AgentSpec:
    slug: str
    name: str
    category: str
    icon: str
    one_liner: str
    description: str
    prefix: str
    example_prompts: tuple[str, ...] = field(default_factory=tuple)


CATEGORIES: list[dict] = [
    {
        "key": "research",
        "name": "Artist Research & Discovery",
        "blurb": "Discover artists, compare careers, and explore exhibition histories.",
        "icon": "~",
    },
    {
        "key": "market",
        "name": "Market Intelligence",
        "blurb": "Auction trends, price movements, and sector analytics.",
        "icon": "#",
    },
    {
        "key": "advisory",
        "name": "Collection Advisory",
        "blurb": "Acquisition recommendations and portfolio analysis.",
        "icon": "+",
    },
    {
        "key": "valuation",
        "name": "Valuation & Provenance",
        "blurb": "Fair value estimation and ownership history research.",
        "icon": "*",
    },
]


AGENTS: tuple[AgentSpec, ...] = (
    # Research
    AgentSpec(
        slug="artist_lookup", name="Artist Lookup",
        category="research", icon="~", prefix="artist:",
        one_liner="Artist bio, exhibitions, and auction history via web search.",
        description="Searches the web for comprehensive artist information including biography, exhibition history, gallery representation, auction results, and critical reception.",
        example_prompts=(
            "artist: Konrad Magi",
            "artist: Tell me about Gerhard Richter's market trajectory",
            "Who is Adamson-Eric and what are his major works?",
            "artist: Karin Luts biography and exhibitions",
        ),
    ),
    AgentSpec(
        slug="artist_compare", name="Artist Compare",
        category="research", icon="~", prefix="compare:",
        one_liner="Side-by-side comparison of artists by market performance and style.",
        description="Compares two or more artists across dimensions like market performance, auction prices, medium, period, critical reception, and collectibility.",
        example_prompts=(
            "compare: Konrad Magi vs Ants Laikmaa",
            "compare: How does Adamson-Eric's market compare to Juri Arrak?",
            "Compare Baltic modernists by auction performance",
            "compare: Richter vs Kiefer investment returns",
        ),
    ),
    # Market
    AgentSpec(
        slug="market_analyst", name="Market Analyst",
        category="market", icon="#", prefix="market:",
        one_liner="Auction trends, price movements, and sector heat maps.",
        description="Analyzes art market trends including auction price movements, sector performance, medium popularity, and emerging market signals. Can generate charts and visualizations.",
        example_prompts=(
            "market: top selling Estonian artists by total sales",
            "market: oil painting price trends over the last decade",
            "What's the overbid percentage for Baltic art?",
            "market: which art categories are trending up?",
        ),
    ),
    AgentSpec(
        slug="auction_tracker", name="Auction Tracker",
        category="market", icon="#", prefix="auction:",
        one_liner="Track specific lots, sales, and Estonian auction data.",
        description="Tracks auction lots and results from Estonian auction houses (Allee Galerii, Haus). Provides detailed sale data, price comparisons, and lot-level analytics.",
        example_prompts=(
            "auction: recent sales of August Jansen works",
            "auction: what sold at Haus gallery last year?",
            "Show me the highest-priced lots from Allee Galerii",
            "auction: watercolour sales trends",
        ),
    ),
    # Advisory
    AgentSpec(
        slug="acquisition_advisor", name="Acquisition Advisor",
        category="advisory", icon="+", prefix="advise:",
        one_liner="Recommend acquisitions based on collection goals and budget.",
        description="Provides art acquisition recommendations tailored to your collection goals, budget, risk tolerance, and aesthetic preferences. Considers market trends, artist trajectories, and diversification.",
        example_prompts=(
            "advise: I have EUR 50,000 budget for Estonian art, what should I buy?",
            "advise: best emerging artists for long-term appreciation",
            "Recommend paintings under EUR 10,000 with growth potential",
            "advise: I want to build a Baltic modernist collection",
        ),
    ),
    AgentSpec(
        slug="portfolio_analyst", name="Portfolio Analyst",
        category="advisory", icon="+", prefix="portfolio:",
        one_liner="Analyze holdings, diversification gaps, and rebalancing suggestions.",
        description="Analyzes your art portfolio for diversification across periods, mediums, price tiers, and geographies. Identifies concentration risks and suggests rebalancing opportunities.",
        example_prompts=(
            "portfolio: analyze my current holdings",
            "portfolio: am I too concentrated in oil paintings?",
            "What's my portfolio diversification score?",
            "portfolio: suggest rebalancing for my collection",
        ),
    ),
    # Valuation
    AgentSpec(
        slug="valuator", name="Valuator",
        category="valuation", icon="*", prefix="value:",
        one_liner="Estimate fair value from comparable sales and market conditions.",
        description="Estimates the fair market value of artworks using comparable auction results, artist market trajectory, condition, provenance, and current market conditions.",
        example_prompts=(
            "value: Konrad Magi oil on canvas, 60x80cm, 1920s landscape",
            "value: what's a Richard Uutmaa worth today?",
            "Estimate value of an Adamson-Eric tempera, 40x50cm",
            "value: August Jansen 1945 oil painting",
        ),
    ),
    AgentSpec(
        slug="provenance_checker", name="Provenance Checker",
        category="valuation", icon="*", prefix="provenance:",
        one_liner="Research ownership history, exhibition record, and authenticity signals.",
        description="Researches the provenance and exhibition history of artworks and artists. Checks for red flags, verifies exhibition records, and assesses authenticity indicators.",
        example_prompts=(
            "provenance: research the ownership history of Konrad Magi landscapes",
            "provenance: where has this artist exhibited?",
            "Check exhibition history for Ants Laikmaa",
            "provenance: authenticity considerations for Estonian Impressionist works",
        ),
    ),
)

AGENTS_BY_SLUG: dict[str, AgentSpec] = {a.slug: a for a in AGENTS}


def by_slug(slug: str) -> AgentSpec | None:
    return AGENTS_BY_SLUG.get(slug)
