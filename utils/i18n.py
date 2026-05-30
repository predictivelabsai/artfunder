"""Internationalisation — session-based language with IP detection.

Ported from plai/pehero. Kanvas supports 5 languages:
en (English), et (Estonian), de (German), fr (French), sv (Swedish).
"""

from __future__ import annotations

from typing import Any

DEFAULT_LANG = "en"

LANGUAGES: dict[str, dict] = {
    "en": {"name": "English",  "native": "English",  "flag": "\U0001f1ec\U0001f1e7"},
    "et": {"name": "Estonian", "native": "Eesti",    "flag": "\U0001f1ea\U0001f1ea"},
    "de": {"name": "German",   "native": "Deutsch",  "flag": "\U0001f1e9\U0001f1ea"},
    "fr": {"name": "French",   "native": "Français", "flag": "\U0001f1eb\U0001f1f7"},
    "sv": {"name": "Swedish",  "native": "Svenska",  "flag": "\U0001f1f8\U0001f1ea"},
}

SUPPORTED_LANGS = set(LANGUAGES.keys())

_ESTONIAN_IP_PREFIXES = (
    "85.253.", "90.190.", "84.50.", "213.168.", "195.50.",
    "62.65.", "88.196.", "86.43.", "193.40.", "194.126.",
)


def _get_client_ip(request) -> str:
    forwarded = (getattr(request, "headers", {}) or {}).get("x-forwarded-for", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    client = getattr(request, "client", None)
    return client.host if client else ""


def detect_language(request) -> str:
    ip = _get_client_ip(request)
    if any(ip.startswith(p) for p in _ESTONIAN_IP_PREFIXES):
        return "et"
    return DEFAULT_LANG


def get_lang(sess: dict[str, Any], request=None) -> str:
    lang = (sess.get("lang") or "").lower()
    if lang in SUPPORTED_LANGS:
        return lang
    if request:
        detected = detect_language(request)
        sess["lang"] = detected
        return detected
    return DEFAULT_LANG


def set_lang(sess: dict[str, Any], lang: str) -> str:
    code = (lang or "").lower()
    if code in SUPPORTED_LANGS:
        sess["lang"] = code
    return get_lang(sess)


def t(key: str, lang: str = DEFAULT_LANG) -> str:
    entry = TRANSLATIONS.get(key)
    if not entry:
        return key
    return entry.get(lang, entry.get("en", key))


def agent_t(slug: str, field: str, lang: str = DEFAULT_LANG) -> str:
    entry = AGENT_TRANSLATIONS.get(slug, {}).get(field)
    if not entry:
        return slug if field == "name" else ""
    return entry.get(lang, entry.get("en", slug))


def category_t(key: str, field: str, lang: str = DEFAULT_LANG) -> str:
    entry = CATEGORY_TRANSLATIONS.get(key, {}).get(field)
    if not entry:
        return key if field == "name" else ""
    return entry.get(lang, entry.get("en", key))


def js_translations(lang: str = DEFAULT_LANG) -> dict[str, str]:
    return {k.removeprefix("js_"): t(k, lang)
            for k in TRANSLATIONS if k.startswith("js_")}


# ---------------------------------------------------------------------------
# Translation catalog
# ---------------------------------------------------------------------------

TRANSLATIONS: dict[str, dict[str, str]] = {

    # ── Navigation ────────────────────────────────────────────
    "nav_home": {
        "en": "Home", "et": "Avaleht", "de": "Startseite",
        "fr": "Accueil", "sv": "Hem",
    },
    "nav_advisory": {
        "en": "Advisory", "et": "Nõustamine", "de": "Beratung",
        "fr": "Conseil", "sv": "Rådgivning",
    },
    "nav_collection": {
        "en": "Collection", "et": "Kogu", "de": "Sammlung",
        "fr": "Collection", "sv": "Samling",
    },
    "nav_artists": {
        "en": "Artists", "et": "Kunstnikud", "de": "Künstler",
        "fr": "Artistes", "sv": "Konstnärer",
    },
    "nav_about": {
        "en": "About", "et": "Meist", "de": "Über uns",
        "fr": "À propos", "sv": "Om oss",
    },
    "nav_art_index": {
        "en": "Art Index", "et": "Kunstiindeks", "de": "Kunstindex",
        "fr": "Indice Art", "sv": "Konstindex",
    },
    "nav_contact": {
        "en": "Contact", "et": "Kontakt", "de": "Kontakt",
        "fr": "Contact", "sv": "Kontakt",
    },
    "nav_open_app": {
        "en": "Open App", "et": "Ava rakendus", "de": "App öffnen",
        "fr": "Ouvrir l'app", "sv": "Öppna appen",
    },
    "nav_login": {
        "en": "Login", "et": "Logi sisse", "de": "Anmelden",
        "fr": "Connexion", "sv": "Logga in",
    },
    "nav_logout": {
        "en": "Log Out", "et": "Logi välja", "de": "Abmelden",
        "fr": "Déconnexion", "sv": "Logga ut",
    },

    # ── Hero ──────────────────────────────────────────────────
    "hero_h1": {
        "en": "Your AI Art Advisor.",
        "et": "Sinu tehisintellektist kunstinõustaja.",
        "de": "Ihr KI-Kunstberater.",
        "fr": "Votre conseiller artistique IA.",
        "sv": "Din AI-konstrådgivare.",
    },
    "hero_h2": {
        "en": "Track, value, and grow your collection.",
        "et": "Jälgi, väärtusta ja kasva oma kogu.",
        "de": "Verfolgen, bewerten und erweitern Sie Ihre Sammlung.",
        "fr": "Suivez, évaluez et développez votre collection.",
        "sv": "Spåra, värdera och utveckla din samling.",
    },
    "hero_body": {
        "en": "AI-powered art advisory combining market intelligence, auction analytics, and collection management. From artist research to acquisition strategy.",
        "et": "Tehisintellektil põhinev kunstinõustamine, mis ühendab turuluure, oksjoni analüütika ja kogu haldamise. Kunstniku uurimisest omandamisstrateegiani.",
        "de": "KI-gestützte Kunstberatung mit Marktintelligenz, Auktionsanalysen und Sammlungsmanagement. Von der Künstlerrecherche bis zur Akquisitionsstrategie.",
        "fr": "Conseil artistique propulsé par l'IA combinant intelligence de marché, analyse d'enchères et gestion de collection. De la recherche d'artistes à la stratégie d'acquisition.",
        "sv": "AI-driven konstrådgivning som kombinerar marknadsintelligens, auktionsanalys och samlingshantering. Från konstnärsforskning till förvärvsstrategi.",
    },
    "hero_cta_start": {
        "en": "Start Advisory Session", "et": "Alusta nõustamist",
        "de": "Beratung starten", "fr": "Démarrer une session",
        "sv": "Starta rådgivning",
    },
    "hero_cta_explore": {
        "en": "Explore Collection", "et": "Avasta kogu",
        "de": "Sammlung erkunden", "fr": "Explorer la collection",
        "sv": "Utforska samlingen",
    },

    # ── Features ──────────────────────────────────────────────
    "feat_advisory": {
        "en": "Advisory", "et": "Nõustamine", "de": "Beratung",
        "fr": "Conseil", "sv": "Rådgivning",
    },
    "feat_advisory_body": {
        "en": "AI-powered recommendations from 8 specialist agents. Research artists, compare market performance, and get acquisition advice tailored to your goals.",
        "et": "Tehisintellekti soovitused 8 erialagendilt. Uuri kunstnikke, võrdle turutulemusi ja saa omandamisnõu vastavalt oma eesmärkidele.",
        "de": "KI-gestützte Empfehlungen von 8 Spezialagenten. Recherchieren Sie Künstler, vergleichen Sie Marktleistungen und erhalten Sie maßgeschneiderte Akquisitionsberatung.",
        "fr": "Recommandations IA de 8 agents spécialisés. Recherchez des artistes, comparez les performances du marché et obtenez des conseils d'acquisition adaptés.",
        "sv": "AI-drivna rekommendationer från 8 specialistagenter. Forska om konstnärer, jämför marknadsprestanda och få förvärvsråd anpassade till dina mål.",
    },
    "feat_advisory_link": {
        "en": "Start a conversation", "et": "Alusta vestlust",
        "de": "Gespräch starten", "fr": "Démarrer une conversation",
        "sv": "Starta en konversation",
    },
    "feat_market": {
        "en": "Market Intelligence", "et": "Turuluure",
        "de": "Marktintelligenz", "fr": "Intelligence de marché",
        "sv": "Marknadsintelligens",
    },
    "feat_market_body": {
        "en": "Real-time auction analytics, price trend visualizations, and sector heat maps. Track Estonian and international art markets with interactive Plotly charts.",
        "et": "Reaalajas oksjoni analüütika, hinnatrendide visualiseeringud ja sektori kuumuskaardid. Jälgi Eesti ja rahvusvahelist kunstiturgu interaktiivsete graafikutega.",
        "de": "Echtzeit-Auktionsanalysen, Preistrendvisualisierungen und Sektor-Heatmaps. Verfolgen Sie estnische und internationale Kunstmärkte mit interaktiven Plotly-Diagrammen.",
        "fr": "Analyses d'enchères en temps réel, visualisations des tendances de prix et cartes sectorielles. Suivez les marchés estonien et international avec des graphiques interactifs.",
        "sv": "Auktionsanalyser i realtid, pristrendvisualiseringar och sektorsvärmekartor. Följ estniska och internationella konstmarknader med interaktiva Plotly-diagram.",
    },
    "feat_market_link": {
        "en": "View market map", "et": "Vaata turukaart",
        "de": "Marktkarte ansehen", "fr": "Voir la carte du marché",
        "sv": "Se marknadskarta",
    },
    "feat_collection": {
        "en": "Collection Management", "et": "Kogu haldamine",
        "de": "Sammlungsmanagement", "fr": "Gestion de collection",
        "sv": "Samlingshantering",
    },
    "feat_collection_body": {
        "en": "Track your portfolio, manage fractional ownership positions, and monitor artwork valuations. Diversification analysis and rebalancing suggestions.",
        "et": "Jälgi oma portfelli, halda murdomanduse positsioone ja jälgi teoste hindamisi. Hajutamise analüüs ja tasakaalustamise soovitused.",
        "de": "Verfolgen Sie Ihr Portfolio, verwalten Sie Bruchteilseigentum und überwachen Sie Kunstwerkbewertungen. Diversifikationsanalyse und Rebalancing-Vorschläge.",
        "fr": "Suivez votre portefeuille, gérez vos positions de propriété fractionnaire et surveillez les valorisations. Analyse de diversification et suggestions de rééquilibrage.",
        "sv": "Spåra din portfölj, hantera delat ägande och övervaka konstvärderingar. Diversifieringsanalys och ombalanseringsförslag.",
    },
    "feat_collection_link": {
        "en": "View collection", "et": "Vaata kogu",
        "de": "Sammlung ansehen", "fr": "Voir la collection",
        "sv": "Se samling",
    },

    # ── How It Works ──────────────────────────────────────────
    "how_title": {
        "en": "How It Works", "et": "Kuidas see töötab",
        "de": "So funktioniert es", "fr": "Comment ça marche",
        "sv": "Så fungerar det",
    },
    "how_subtitle": {
        "en": "Three steps to smarter art collecting.",
        "et": "Kolm sammu nutikamaks kunsti kogumiseks.",
        "de": "Drei Schritte zum intelligenteren Kunstsammeln.",
        "fr": "Trois étapes pour collectionner plus intelligemment.",
        "sv": "Tre steg till smartare konstsamlande.",
    },
    "how_01_title": {
        "en": "Ask", "et": "Küsi", "de": "Fragen",
        "fr": "Demandez", "sv": "Fråga",
    },
    "how_01_body": {
        "en": "Ask any question about an artist, artwork, market trend, or collection strategy. Our AI routes your query to the right specialist agent.",
        "et": "Esita küsimus kunstniku, teose, turutrendi või kogumisstrateegia kohta. Meie tehisintellekt suunab päringu õigele erialagendile.",
        "de": "Stellen Sie Fragen zu einem Künstler, Kunstwerk, Markttrend oder Sammlungsstrategie. Unsere KI leitet Ihre Anfrage an den richtigen Spezialagenten weiter.",
        "fr": "Posez n'importe quelle question sur un artiste, une œuvre, une tendance ou une stratégie de collection. Notre IA dirige votre demande vers l'agent spécialiste adéquat.",
        "sv": "Ställ vilken fråga som helst om en konstnär, konstverk, marknadstrend eller samlingsstrategi. Vår AI dirigerar din fråga till rätt specialistagent.",
    },
    "how_02_title": {
        "en": "Analyze", "et": "Analüüsi", "de": "Analysieren",
        "fr": "Analysez", "sv": "Analysera",
    },
    "how_02_body": {
        "en": "The agent searches auction databases, scrapes market data, and generates visualizations. Results stream in real-time with full transparency.",
        "et": "Agent otsib oksjoni andmebaasidest, kogub turuandmeid ja loob visualiseeringuid. Tulemused voolavad reaalajas täieliku läbipaistvusega.",
        "de": "Der Agent durchsucht Auktionsdatenbanken, sammelt Marktdaten und erstellt Visualisierungen. Ergebnisse werden in Echtzeit mit voller Transparenz gestreamt.",
        "fr": "L'agent interroge les bases de données d'enchères, collecte les données de marché et génère des visualisations. Les résultats sont diffusés en temps réel.",
        "sv": "Agenten söker i auktionsdatabaser, samlar marknadsdata och skapar visualiseringar. Resultaten strömmas i realtid med full transparens.",
    },
    "how_03_title": {
        "en": "Act", "et": "Tegutse", "de": "Handeln",
        "fr": "Agissez", "sv": "Agera",
    },
    "how_03_body": {
        "en": "Get actionable recommendations: buy, hold, or diversify. Track acquisitions in your portfolio with ongoing valuation updates.",
        "et": "Saa tegevuspõhiseid soovitusi: osta, hoia või hajuta. Jälgi omandamisi oma portfellis pidevate hindamisvärskendustega.",
        "de": "Erhalten Sie umsetzbare Empfehlungen: kaufen, halten oder diversifizieren. Verfolgen Sie Akquisitionen in Ihrem Portfolio mit laufenden Bewertungsaktualisierungen.",
        "fr": "Obtenez des recommandations concrètes : acheter, conserver ou diversifier. Suivez les acquisitions dans votre portefeuille avec des mises à jour de valorisation.",
        "sv": "Få handlingsbara rekommendationer: köp, behåll eller diversifiera. Spåra förvärv i din portfölj med löpande värderingsuppdateringar.",
    },

    # ── Agents Preview ────────────────────────────────────────
    "agents_title": {
        "en": "8 Specialist Agents", "et": "8 erialagenti",
        "de": "8 Spezialagenten", "fr": "8 agents spécialisés",
        "sv": "8 specialistagenter",
    },
    "agents_subtitle": {
        "en": "Each trained for a specific aspect of art advisory.",
        "et": "Igaüks koolitatud konkreetse kunstinõustamise valdkonna jaoks.",
        "de": "Jeder für einen spezifischen Aspekt der Kunstberatung ausgebildet.",
        "fr": "Chacun formé pour un aspect spécifique du conseil artistique.",
        "sv": "Var och en utbildad för en specifik aspekt av konstrådgivning.",
    },

    # ── Stats ─────────────────────────────────────────────────
    "stat_return": {
        "en": "Avg. Net Return", "et": "Keskm. netotootlus",
        "de": "Durchschn. Nettorendite", "fr": "Rendement net moy.",
        "sv": "Genomsn. nettoavkastning",
    },
    "stat_distributions": {
        "en": "Investor Distributions", "et": "Investori väljamaksed",
        "de": "Investorenausschüttungen", "fr": "Distributions aux investisseurs",
        "sv": "Investerardistributioner",
    },
    "stat_aum": {
        "en": "Art Under Management", "et": "Hallatav kunst",
        "de": "Kunst unter Verwaltung", "fr": "Art sous gestion",
        "sv": "Konst under förvaltning",
    },
    "stat_collectors": {
        "en": "Collectors", "et": "Kogujad", "de": "Sammler",
        "fr": "Collectionneurs", "sv": "Samlare",
    },
    "stat_artworks": {
        "en": "Artworks Funded", "et": "Rahastatud teosed",
        "de": "Finanzierte Kunstwerke", "fr": "Œuvres financées",
        "sv": "Finansierade konstverk",
    },
    "stat_countries": {
        "en": "Countries", "et": "Riigid", "de": "Länder",
        "fr": "Pays", "sv": "Länder",
    },

    # ── CTA ───────────────────────────────────────────────────
    "cta_headline": {
        "en": "Start collecting smarter.",
        "et": "Alusta nutikamat kogumist.",
        "de": "Beginnen Sie intelligenter zu sammeln.",
        "fr": "Commencez à collectionner plus intelligemment.",
        "sv": "Börja samla smartare.",
    },
    "cta_body": {
        "en": "Join over 12,000 European collectors using AI-powered art advisory.",
        "et": "Ühine üle 12 000 Euroopa kogujaga, kes kasutavad tehisintellektil põhinevat kunstinõustamist.",
        "de": "Schließen Sie sich über 12.000 europäischen Sammlern an, die KI-gestützte Kunstberatung nutzen.",
        "fr": "Rejoignez plus de 12 000 collectionneurs européens utilisant le conseil artistique par IA.",
        "sv": "Gå med över 12 000 europeiska samlare som använder AI-driven konstrådgivning.",
    },
    "cta_create_account": {
        "en": "Create Account", "et": "Loo konto", "de": "Konto erstellen",
        "fr": "Créer un compte", "sv": "Skapa konto",
    },

    # ── Partners ──────────────────────────────────────────────
    "supported_by": {
        "en": "Supported by", "et": "Toetab", "de": "Unterstützt von",
        "fr": "Soutenu par", "sv": "Stöds av",
    },

    # ── Footer ────────────────────────────────────────────────
    "footer_desc": {
        "en": "AI-powered art advisory and investment platform. We connect collectors with expertly curated artworks, market intelligence, and fractional ownership opportunities.",
        "et": "Tehisintellektil põhinev kunstinõustamise ja investeerimise platvorm. Ühendame kogujad ekspertide poolt kureeritud teoste, turuluure ja murdomanduse võimalustega.",
        "de": "KI-gestützte Kunstberatungs- und Investitionsplattform. Wir verbinden Sammler mit fachmännisch kuratierten Kunstwerken, Marktintelligenz und Bruchteilseigentum.",
        "fr": "Plateforme de conseil et d'investissement artistique par IA. Nous connectons les collectionneurs avec des œuvres d'art sélectionnées, l'intelligence de marché et la propriété fractionnaire.",
        "sv": "AI-driven plattform för konstrådgivning och investering. Vi kopplar samman samlare med expertutvalda konstverk, marknadsintelligens och delat ägande.",
    },
    "footer_platform": {
        "en": "Platform", "et": "Platvorm", "de": "Plattform",
        "fr": "Plateforme", "sv": "Plattform",
    },
    "footer_resources": {
        "en": "Resources", "et": "Ressursid", "de": "Ressourcen",
        "fr": "Ressources", "sv": "Resurser",
    },
    "footer_legal": {
        "en": "Legal", "et": "Juriidiline", "de": "Rechtliches",
        "fr": "Légal", "sv": "Juridiskt",
    },
    "footer_for_artists": {
        "en": "For Artists", "et": "Kunstnikele", "de": "Für Künstler",
        "fr": "Pour les artistes", "sv": "För konstnärer",
    },
    "footer_terms": {
        "en": "Terms of Service", "et": "Teenuse tingimused",
        "de": "Nutzungsbedingungen", "fr": "Conditions d'utilisation",
        "sv": "Användarvillkor",
    },
    "footer_privacy": {
        "en": "Privacy Policy", "et": "Privaatsuspoliitika",
        "de": "Datenschutzrichtlinie", "fr": "Politique de confidentialité",
        "sv": "Integritetspolicy",
    },
    "footer_risk": {
        "en": "Risk Disclosures", "et": "Riskiavaldused",
        "de": "Risikohinweise", "fr": "Divulgation des risques",
        "sv": "Riskupplysningar",
    },
    "footer_copyright": {
        "en": "© 2026 Kanvas.ai. All rights reserved.",
        "et": "© 2026 Kanvas.ai. Kõik õigused kaitstud.",
        "de": "© 2026 Kanvas.ai. Alle Rechte vorbehalten.",
        "fr": "© 2026 Kanvas.ai. Tous droits réservés.",
        "sv": "© 2026 Kanvas.ai. Alla rättigheter förbehållna.",
    },
    "footer_disclaimer": {
        "en": "Art advisory and investment involve risk. Past performance does not guarantee future results.",
        "et": "Kunstinõustamine ja investeerimine on seotud riskiga. Varasemad tulemused ei taga tulevasi tulemusi.",
        "de": "Kunstberatung und Investitionen sind mit Risiken verbunden. Vergangene Wertentwicklungen garantieren keine zukünftigen Ergebnisse.",
        "fr": "Le conseil artistique et l'investissement comportent des risques. Les performances passées ne garantissent pas les résultats futurs.",
        "sv": "Konstrådgivning och investeringar innebär risk. Tidigare resultat garanterar inte framtida avkastning.",
    },

    # ── Chat UI ───────────────────────────────────────────────
    "chat_new": {
        "en": "+ New chat", "et": "+ Uus vestlus", "de": "+ Neuer Chat",
        "fr": "+ Nouveau chat", "sv": "+ Ny chatt",
    },
    "chat_history": {
        "en": "History", "et": "Ajalugu", "de": "Verlauf",
        "fr": "Historique", "sv": "Historik",
    },
    "chat_no_sessions": {
        "en": "No conversations yet.", "et": "Vestlused puuduvad.",
        "de": "Noch keine Unterhaltungen.", "fr": "Aucune conversation.",
        "sv": "Inga konversationer än.",
    },
    "chat_agents": {
        "en": "Agents", "et": "Agendid", "de": "Agenten",
        "fr": "Agents", "sv": "Agenter",
    },
    "chat_sign_in": {
        "en": "Sign in", "et": "Logi sisse", "de": "Anmelden",
        "fr": "Se connecter", "sv": "Logga in",
    },
    "chat_sign_out": {
        "en": "Sign out", "et": "Logi välja", "de": "Abmelden",
        "fr": "Se déconnecter", "sv": "Logga ut",
    },
    "chat_welcome_title": {
        "en": "Kanvas.ai Art Advisor",
        "et": "Kanvas.ai kunstinõustaja",
        "de": "Kanvas.ai Kunstberater",
        "fr": "Kanvas.ai Conseiller Artistique",
        "sv": "Kanvas.ai Konstrådgivare",
    },
    "chat_welcome_body": {
        "en": "Ask about artists, market trends, valuations, or collection strategy.",
        "et": "Küsi kunstnike, turutrendide, hindamiste või kogumisstrateegia kohta.",
        "de": "Fragen Sie nach Künstlern, Markttrends, Bewertungen oder Sammlungsstrategie.",
        "fr": "Posez des questions sur les artistes, les tendances, les évaluations ou la stratégie de collection.",
        "sv": "Fråga om konstnärer, marknadstrender, värderingar eller samlingsstrategi.",
    },
    "chat_placeholder": {
        "en": "Ask about an artist, market trends, or get advisory...",
        "et": "Küsi kunstniku, turutrendide kohta või saa nõu...",
        "de": "Fragen Sie nach einem Künstler, Markttrends oder lassen Sie sich beraten...",
        "fr": "Posez une question sur un artiste, les tendances du marché ou obtenez des conseils...",
        "sv": "Fråga om en konstnär, marknadstrender eller få rådgivning...",
    },
    "chat_copy": {
        "en": "Copy", "et": "Kopeeri", "de": "Kopieren",
        "fr": "Copier", "sv": "Kopiera",
    },
    "chat_canvas": {
        "en": "Canvas", "et": "Lõuend", "de": "Leinwand",
        "fr": "Canevas", "sv": "Canvas",
    },
    "chat_signin_title": {
        "en": "Sign in to Kanvas.ai",
        "et": "Logi sisse Kanvas.ai",
        "de": "Bei Kanvas.ai anmelden",
        "fr": "Se connecter à Kanvas.ai",
        "sv": "Logga in på Kanvas.ai",
    },
    "chat_signin_body": {
        "en": "Enter your email to save chat history.",
        "et": "Sisesta oma e-post vestluste salvestamiseks.",
        "de": "Geben Sie Ihre E-Mail ein, um den Chatverlauf zu speichern.",
        "fr": "Entrez votre e-mail pour sauvegarder l'historique.",
        "sv": "Ange din e-post för att spara chatthistorik.",
    },
    "chat_cancel": {
        "en": "Cancel", "et": "Tühista", "de": "Abbrechen",
        "fr": "Annuler", "sv": "Avbryt",
    },
    "chat_news_title": {
        "en": "Art News", "et": "Kunstiuudised", "de": "Kunstnachrichten",
        "fr": "Actualités Art", "sv": "Konstnyheter",
    },
    "chat_news_subtitle": {
        "en": "Estonian & Baltic art market",
        "et": "Eesti ja Balti kunstiturug",
        "de": "Estnischer & baltischer Kunstmarkt",
        "fr": "Marché de l'art estonien et balte",
        "sv": "Estnisk & baltisk konstmarknad",
    },

    # ── JS strings (prefixed js_ → exported without prefix) ──
    "js_thinking": {
        "en": "Thinking", "et": "Mõtleb", "de": "Denkt nach",
        "fr": "Réflexion", "sv": "Tänker",
    },
    "js_calling": {
        "en": "Calling", "et": "Kutsub", "de": "Ruft auf",
        "fr": "Appel", "sv": "Anropar",
    },
    "js_copy_csv": {
        "en": "Copy CSV", "et": "Kopeeri CSV", "de": "CSV kopieren",
        "fr": "Copier CSV", "sv": "Kopiera CSV",
    },
    "js_download_csv": {
        "en": "Download CSV", "et": "Laadi CSV", "de": "CSV herunterladen",
        "fr": "Télécharger CSV", "sv": "Ladda ner CSV",
    },
    "js_copied": {
        "en": "Copied!", "et": "Kopeeritud!", "de": "Kopiert!",
        "fr": "Copié !", "sv": "Kopierat!",
    },
    "js_loading_news": {
        "en": "Loading art news...", "et": "Kunstiuudiste laadimine...",
        "de": "Kunstnachrichten laden...", "fr": "Chargement des actualités...",
        "sv": "Laddar konstnyheter...",
    },
}

# ── Agent translations ────────────────────────────────────────
AGENT_TRANSLATIONS: dict[str, dict[str, dict[str, str]]] = {
    "artist_lookup": {
        "name": {"en": "Artist Lookup", "et": "Kunstniku otsing", "de": "Künstlersuche", "fr": "Recherche d'artiste", "sv": "Konstnärssökning"},
        "one_liner": {"en": "Biography, exhibitions, and auction history via web search.", "et": "Biograafia, näitused ja oksjoniajalugu veebiotsingu kaudu.", "de": "Biografie, Ausstellungen und Auktionsgeschichte.", "fr": "Biographie, expositions et historique des enchères.", "sv": "Biografi, utställningar och auktionshistorik."},
    },
    "artist_compare": {
        "name": {"en": "Artist Compare", "et": "Kunstnike võrdlus", "de": "Künstlervergleich", "fr": "Comparaison d'artistes", "sv": "Konstnärsjämförelse"},
        "one_liner": {"en": "Side-by-side comparison by market performance and style.", "et": "Kõrvutivõrdlus turutulemuste ja stiili alusel.", "de": "Vergleich nach Marktleistung und Stil.", "fr": "Comparaison par performance et style.", "sv": "Jämförelse efter marknadsprestanda och stil."},
    },
    "market_analyst": {
        "name": {"en": "Market Analyst", "et": "Turuanalüütik", "de": "Marktanalyst", "fr": "Analyste de marché", "sv": "Marknadsanalytiker"},
        "one_liner": {"en": "Auction trends, price movements, and sector analytics.", "et": "Oksjonitrendid, hinnaliikumised ja sektori analüütika.", "de": "Auktionstrends, Preisbewegungen und Sektoranalysen.", "fr": "Tendances des enchères, mouvements de prix et analyses sectorielles.", "sv": "Auktionstrender, prisrörelser och sektorsanalys."},
    },
    "auction_tracker": {
        "name": {"en": "Auction Tracker", "et": "Oksjoni jälgija", "de": "Auktionstracker", "fr": "Suivi d'enchères", "sv": "Auktionsspårare"},
        "one_liner": {"en": "Track lots and results from Estonian auction houses.", "et": "Jälgi partii sid ja tulemusi Eesti oksjonimajadest.", "de": "Lose und Ergebnisse estnischer Auktionshäuser verfolgen.", "fr": "Suivre les lots et résultats des maisons de vente estoniennes.", "sv": "Spåra poster och resultat från estniska auktionshus."},
    },
    "acquisition_advisor": {
        "name": {"en": "Acquisition Advisor", "et": "Omandamise nõustaja", "de": "Akquisitionsberater", "fr": "Conseiller en acquisition", "sv": "Förvärvsrådgivare"},
        "one_liner": {"en": "Recommendations based on goals, budget, and preferences.", "et": "Soovitused eesmärkide, eelarve ja eelistuste alusel.", "de": "Empfehlungen basierend auf Zielen, Budget und Präferenzen.", "fr": "Recommandations selon objectifs, budget et préférences.", "sv": "Rekommendationer baserade på mål, budget och preferenser."},
    },
    "portfolio_analyst": {
        "name": {"en": "Portfolio Analyst", "et": "Portfelli analüütik", "de": "Portfolioanalyst", "fr": "Analyste de portefeuille", "sv": "Portföljanalytiker"},
        "one_liner": {"en": "Diversification analysis and rebalancing suggestions.", "et": "Hajutamise analüüs ja tasakaalustamise soovitused.", "de": "Diversifikationsanalyse und Rebalancing-Vorschläge.", "fr": "Analyse de diversification et suggestions de rééquilibrage.", "sv": "Diversifieringsanalys och ombalanseringsförslag."},
    },
    "valuator": {
        "name": {"en": "Valuator", "et": "Hindaja", "de": "Bewerter", "fr": "Évaluateur", "sv": "Värderare"},
        "one_liner": {"en": "Fair value estimation from comparable sales and market data.", "et": "Õiglase väärtuse hindamine võrreldavate müükide ja turuandmete põhjal.", "de": "Marktwertschätzung aus vergleichbaren Verkäufen und Marktdaten.", "fr": "Estimation de la juste valeur à partir de ventes comparables.", "sv": "Marknadsvärdering från jämförbara försäljningar."},
    },
    "provenance_checker": {
        "name": {"en": "Provenance Checker", "et": "Päritolu kontrollija", "de": "Provenienzprüfer", "fr": "Vérificateur de provenance", "sv": "Provenienskontrollant"},
        "one_liner": {"en": "Ownership history and authenticity research.", "et": "Omaniku ajalugu ja autentsuse uurimine.", "de": "Eigentumsgeschichte und Authentizitätsforschung.", "fr": "Historique de propriété et recherche d'authenticité.", "sv": "Ägarhistorik och autenticitetsforskning."},
    },
}

# ── Category translations ─────────────────────────────────────
CATEGORY_TRANSLATIONS: dict[str, dict[str, dict[str, str]]] = {
    "research": {
        "name": {"en": "Artist Research & Discovery", "et": "Kunstniku uurimine", "de": "Künstlerrecherche", "fr": "Recherche d'artistes", "sv": "Konstnärsforskning"},
    },
    "market": {
        "name": {"en": "Market Intelligence", "et": "Turuluure", "de": "Marktintelligenz", "fr": "Intelligence de marché", "sv": "Marknadsintelligens"},
    },
    "advisory": {
        "name": {"en": "Collection Advisory", "et": "Kogu nõustamine", "de": "Sammlungsberatung", "fr": "Conseil de collection", "sv": "Samlingsrådgivning"},
    },
    "valuation": {
        "name": {"en": "Valuation & Provenance", "et": "Hindamine ja päritolu", "de": "Bewertung & Provenienz", "fr": "Évaluation & Provenance", "sv": "Värdering & Proveniens"},
    },
}
