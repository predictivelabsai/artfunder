from fasthtml.common import *
from utils.i18n import t, agent_t, get_lang


def home_page(sess=None):
    from utils.config import settings
    login_enabled = settings().login_enabled
    lang = get_lang(sess or {})

    agents = [
        "artist_lookup", "artist_compare", "market_analyst", "auction_tracker",
        "acquisition_advisor", "portfolio_analyst", "valuator", "provenance_checker",
    ]

    hero = Section(
        Div(
            Div(
                H1(t('hero_h1', lang),
                   cls='font-display text-5xl md:text-6xl font-bold leading-tight max-w-3xl mb-2 text-black'),
                P(t('hero_h2', lang),
                  cls='font-display text-3xl md:text-4xl text-gray-400 mb-8'),
                P(t('hero_body', lang),
                  cls='text-base max-w-xl text-gray-500 mb-10 leading-relaxed'),
                Div(
                    A(t('hero_cta_start', lang), href='/app',
                      cls='inline-block px-8 py-3 rounded-full font-semibold text-base no-underline bg-black text-white hover:bg-gray-800 transition-colors'),
                    A(t('hero_cta_explore', lang), href='/investors',
                      cls='inline-block px-8 py-3 rounded-full font-semibold text-base no-underline bg-transparent text-black border border-gray-300 hover:border-black transition-colors'),
                    cls='flex gap-4 flex-wrap'
                ),
                cls='max-w-7xl mx-auto'
            ),
            A(
                Img(src='/docs/kanvas.gif',
                    alt='Kanvas.ai product tour',
                    cls='block w-full h-auto rounded-2xl border border-gray-200 shadow-[0_8px_40px_rgba(0,0,0,0.06)]',
                    loading='lazy'),
                href='/app',
                cls='block max-w-5xl mx-auto mt-16 rounded-2xl overflow-hidden hover:opacity-95 transition-opacity',
            ),
        ),
        cls='bg-white py-24 px-8'
    )

    features = Section(
        Div(
            Div(
                Div(
                    H3(t('feat_advisory', lang), cls='text-lg font-bold text-black mb-3'),
                    P(t('feat_advisory_body', lang), cls='text-gray-500 text-sm leading-relaxed'),
                    A(t('feat_advisory_link', lang), href='/app',
                      cls='block mt-4 no-underline font-semibold text-sm text-black'),
                    cls='p-8 border border-gray-100 rounded-lg hover:border-gray-300 transition-colors'
                ),
                Div(
                    H3(t('feat_market', lang), cls='text-lg font-bold text-black mb-3'),
                    P(t('feat_market_body', lang), cls='text-gray-500 text-sm leading-relaxed'),
                    A(t('feat_market_link', lang), href='/app/market-map',
                      cls='block mt-4 no-underline font-semibold text-sm text-black'),
                    cls='p-8 border border-gray-100 rounded-lg hover:border-gray-300 transition-colors'
                ),
                Div(
                    H3(t('feat_collection', lang), cls='text-lg font-bold text-black mb-3'),
                    P(t('feat_collection_body', lang), cls='text-gray-500 text-sm leading-relaxed'),
                    A(t('feat_collection_link', lang), href='/investors',
                      cls='block mt-4 no-underline font-semibold text-sm text-black'),
                    cls='p-8 border border-gray-100 rounded-lg hover:border-gray-300 transition-colors'
                ),
                cls='grid grid-cols-1 md:grid-cols-3 gap-6'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-16 px-8 bg-white'
    )

    how_it_works = Section(
        Div(
            Div(
                H2(t('how_title', lang), cls='font-display text-3xl font-bold text-black mb-4'),
                P(t('how_subtitle', lang), cls='text-base text-gray-500 max-w-xl'),
                cls='mb-12'
            ),
            Div(
                Div(
                    Span('01', cls='text-4xl font-bold text-gray-200 block mb-4'),
                    H3(t('how_01_title', lang), cls='text-lg font-bold text-black mb-3'),
                    P(t('how_01_body', lang), cls='text-gray-500 text-sm leading-relaxed'),
                    cls='p-6'
                ),
                Div(
                    Span('02', cls='text-4xl font-bold text-gray-200 block mb-4'),
                    H3(t('how_02_title', lang), cls='text-lg font-bold text-black mb-3'),
                    P(t('how_02_body', lang), cls='text-gray-500 text-sm leading-relaxed'),
                    cls='p-6'
                ),
                Div(
                    Span('03', cls='text-4xl font-bold text-gray-200 block mb-4'),
                    H3(t('how_03_title', lang), cls='text-lg font-bold text-black mb-3'),
                    P(t('how_03_body', lang), cls='text-gray-500 text-sm leading-relaxed'),
                    cls='p-6'
                ),
                cls='grid grid-cols-1 md:grid-cols-3 gap-6 border-t border-gray-100 pt-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8 bg-gray-50'
    )

    agent_cards = []
    for slug in agents:
        agent_cards.append(Div(
            H4(agent_t(slug, 'name', lang), cls='text-sm font-bold text-black mb-1'),
            P(agent_t(slug, 'one_liner', lang), cls='text-xs text-gray-500'),
            cls='p-4 border border-gray-100 rounded-lg'
        ))

    agents_preview = Section(
        Div(
            Div(
                H2(t('agents_title', lang), cls='font-display text-3xl font-bold text-black mb-4'),
                P(t('agents_subtitle', lang), cls='text-base text-gray-500 max-w-xl'),
                cls='mb-12'
            ),
            Div(*agent_cards, cls='grid grid-cols-2 md:grid-cols-4 gap-4'),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8 bg-white'
    )

    stats = Section(
        Div(
            Div(H3('14.1%', cls='text-3xl font-extrabold text-black mb-1'), P(t('stat_return', lang), cls='text-xs text-gray-400 uppercase tracking-wider'), cls='text-center'),
            Div(H3(chr(8364) + '48M', cls='text-3xl font-extrabold text-black mb-1'), P(t('stat_distributions', lang), cls='text-xs text-gray-400 uppercase tracking-wider'), cls='text-center'),
            Div(H3(chr(8364) + '285M', cls='text-3xl font-extrabold text-black mb-1'), P(t('stat_aum', lang), cls='text-xs text-gray-400 uppercase tracking-wider'), cls='text-center'),
            Div(H3('12,400+', cls='text-3xl font-extrabold text-black mb-1'), P(t('stat_collectors', lang), cls='text-xs text-gray-400 uppercase tracking-wider'), cls='text-center'),
            Div(H3('180+', cls='text-3xl font-extrabold text-black mb-1'), P(t('stat_artworks', lang), cls='text-xs text-gray-400 uppercase tracking-wider'), cls='text-center'),
            Div(H3('18', cls='text-3xl font-extrabold text-black mb-1'), P(t('stat_countries', lang), cls='text-xs text-gray-400 uppercase tracking-wider'), cls='text-center'),
            cls='max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-6 gap-8'
        ),
        cls='bg-gray-50 border-y border-gray-100 py-12 px-8'
    )

    cta = Section(
        Div(
            H2(t('cta_headline', lang), cls='font-display text-3xl font-bold text-black mb-4'),
            P(t('cta_body', lang), cls='text-base text-gray-500 max-w-xl mx-auto mb-8'),
            Div(
                A(t('hero_cta_start', lang), href='/app',
                  cls='inline-block px-8 py-3 rounded-full font-semibold text-base no-underline bg-black text-white hover:bg-gray-800 transition-colors'),
                A(t('cta_create_account', lang) if login_enabled else t('nav_open_app', lang),
                  href='/register' if login_enabled else '/app',
                  cls='inline-block px-8 py-3 rounded-full font-semibold text-base no-underline bg-transparent text-black border border-gray-300 hover:border-black transition-colors'),
                cls='flex gap-4 flex-wrap justify-center'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='bg-white text-center py-20 px-8'
    )

    partners = Section(
        Div(
            P(t('supported_by', lang), cls='text-xs text-gray-400 uppercase tracking-wider mb-4'),
            A('Tezos Foundation', href='https://tezos.foundation/', target='_blank',
              cls='text-sm text-gray-500 no-underline hover:text-black transition-colors font-medium'),
            cls='max-w-7xl mx-auto text-center'
        ),
        cls='py-8 px-8 bg-gray-50 border-t border-gray-100'
    )

    return Div(hero, features, how_it_works, agents_preview, stats, cta, partners)
