from fasthtml.common import *


def home_page():
    from utils.config import settings
    login_enabled = settings().login_enabled

    hero = Section(
        Div(
            Div(
                H1('Your AI Art Advisor.',
                   cls='font-display text-5xl md:text-6xl font-bold leading-tight max-w-3xl mb-2 text-black'),
                P('Track, value, and grow your collection.',
                  cls='font-display text-3xl md:text-4xl text-gray-400 mb-8'),
                P('AI-powered art advisory combining market intelligence, auction analytics, '
                  'and collection management. From artist research to acquisition strategy.',
                  cls='text-base max-w-xl text-gray-500 mb-10 leading-relaxed'),
                Div(
                    A('Start Advisory Session', href='/app',
                      cls='inline-block px-8 py-3 rounded-full font-semibold text-base no-underline bg-black text-white hover:bg-gray-800 transition-colors'),
                    A('Explore Collection', href='/investors',
                      cls='inline-block px-8 py-3 rounded-full font-semibold text-base no-underline bg-transparent text-black border border-gray-300 hover:border-black transition-colors'),
                    cls='flex gap-4 flex-wrap'
                ),
                cls='max-w-7xl mx-auto'
            ),
        ),
        cls='bg-white py-24 px-8'
    )

    features = Section(
        Div(
            Div(
                Div(
                    H3('Advisory', cls='text-lg font-bold text-black mb-3'),
                    P('AI-powered recommendations from 8 specialist agents. Research artists, '
                      'compare market performance, and get acquisition advice tailored to your goals.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    A('Start a conversation', href='/app',
                      cls='block mt-4 no-underline font-semibold text-sm text-black'),
                    cls='p-8 border border-gray-100 rounded-lg hover:border-gray-300 transition-colors'
                ),
                Div(
                    H3('Market Intelligence', cls='text-lg font-bold text-black mb-3'),
                    P('Real-time auction analytics, price trend visualizations, and sector heat maps. '
                      'Track Estonian and international art markets with interactive Plotly charts.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    A('View market map', href='/app/market-map',
                      cls='block mt-4 no-underline font-semibold text-sm text-black'),
                    cls='p-8 border border-gray-100 rounded-lg hover:border-gray-300 transition-colors'
                ),
                Div(
                    H3('Collection Management', cls='text-lg font-bold text-black mb-3'),
                    P('Track your portfolio, manage fractional ownership positions, and monitor '
                      'artwork valuations. Diversification analysis and rebalancing suggestions.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    A('View collection', href='/investors',
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
                H2('How It Works', cls='font-display text-3xl font-bold text-black mb-4'),
                P('Three steps to smarter art collecting.',
                  cls='text-base text-gray-500 max-w-xl'),
                cls='mb-12'
            ),
            Div(
                Div(
                    Span('01', cls='text-4xl font-bold text-gray-200 block mb-4'),
                    H3('Ask', cls='text-lg font-bold text-black mb-3'),
                    P('Ask any question about an artist, artwork, market trend, or collection strategy. '
                      'Our AI routes your query to the right specialist agent.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='p-6'
                ),
                Div(
                    Span('02', cls='text-4xl font-bold text-gray-200 block mb-4'),
                    H3('Analyze', cls='text-lg font-bold text-black mb-3'),
                    P('The agent searches auction databases, scrapes market data, and generates '
                      'visualizations. Results stream in real-time with full transparency.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='p-6'
                ),
                Div(
                    Span('03', cls='text-4xl font-bold text-gray-200 block mb-4'),
                    H3('Act', cls='text-lg font-bold text-black mb-3'),
                    P('Get actionable recommendations: buy, hold, or diversify. Track acquisitions '
                      'in your portfolio with ongoing valuation updates.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='p-6'
                ),
                cls='grid grid-cols-1 md:grid-cols-3 gap-6 border-t border-gray-100 pt-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8 bg-gray-50'
    )

    agents_preview = Section(
        Div(
            Div(
                H2('8 Specialist Agents', cls='font-display text-3xl font-bold text-black mb-4'),
                P('Each trained for a specific aspect of art advisory.',
                  cls='text-base text-gray-500 max-w-xl'),
                cls='mb-12'
            ),
            Div(
                Div(
                    H4('Artist Lookup', cls='text-sm font-bold text-black mb-1'),
                    P('Biography, exhibitions, and auction history via web search.',
                      cls='text-xs text-gray-500'),
                    cls='p-4 border border-gray-100 rounded-lg'
                ),
                Div(
                    H4('Artist Compare', cls='text-sm font-bold text-black mb-1'),
                    P('Side-by-side comparison by market performance and style.',
                      cls='text-xs text-gray-500'),
                    cls='p-4 border border-gray-100 rounded-lg'
                ),
                Div(
                    H4('Market Analyst', cls='text-sm font-bold text-black mb-1'),
                    P('Auction trends, price movements, and sector analytics.',
                      cls='text-xs text-gray-500'),
                    cls='p-4 border border-gray-100 rounded-lg'
                ),
                Div(
                    H4('Auction Tracker', cls='text-sm font-bold text-black mb-1'),
                    P('Track lots and results from Estonian auction houses.',
                      cls='text-xs text-gray-500'),
                    cls='p-4 border border-gray-100 rounded-lg'
                ),
                Div(
                    H4('Acquisition Advisor', cls='text-sm font-bold text-black mb-1'),
                    P('Recommendations based on goals, budget, and preferences.',
                      cls='text-xs text-gray-500'),
                    cls='p-4 border border-gray-100 rounded-lg'
                ),
                Div(
                    H4('Portfolio Analyst', cls='text-sm font-bold text-black mb-1'),
                    P('Diversification analysis and rebalancing suggestions.',
                      cls='text-xs text-gray-500'),
                    cls='p-4 border border-gray-100 rounded-lg'
                ),
                Div(
                    H4('Valuator', cls='text-sm font-bold text-black mb-1'),
                    P('Fair value estimation from comparable sales and market data.',
                      cls='text-xs text-gray-500'),
                    cls='p-4 border border-gray-100 rounded-lg'
                ),
                Div(
                    H4('Provenance Checker', cls='text-sm font-bold text-black mb-1'),
                    P('Ownership history and authenticity research.',
                      cls='text-xs text-gray-500'),
                    cls='p-4 border border-gray-100 rounded-lg'
                ),
                cls='grid grid-cols-2 md:grid-cols-4 gap-4'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8 bg-white'
    )

    stats = Section(
        Div(
            Div(H3('14.1%', cls='text-3xl font-extrabold text-black mb-1'), P('Avg. Net Return', cls='text-xs text-gray-400 uppercase tracking-wider'), cls='text-center'),
            Div(H3('€48M', cls='text-3xl font-extrabold text-black mb-1'), P('Investor Distributions', cls='text-xs text-gray-400 uppercase tracking-wider'), cls='text-center'),
            Div(H3('€285M', cls='text-3xl font-extrabold text-black mb-1'), P('Art Under Management', cls='text-xs text-gray-400 uppercase tracking-wider'), cls='text-center'),
            Div(H3('12,400+', cls='text-3xl font-extrabold text-black mb-1'), P('Collectors', cls='text-xs text-gray-400 uppercase tracking-wider'), cls='text-center'),
            Div(H3('180+', cls='text-3xl font-extrabold text-black mb-1'), P('Artworks Funded', cls='text-xs text-gray-400 uppercase tracking-wider'), cls='text-center'),
            Div(H3('18', cls='text-3xl font-extrabold text-black mb-1'), P('Countries', cls='text-xs text-gray-400 uppercase tracking-wider'), cls='text-center'),
            cls='max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-6 gap-8'
        ),
        cls='bg-gray-50 border-y border-gray-100 py-12 px-8'
    )

    cta = Section(
        Div(
            H2('Start collecting smarter.',
               cls='font-display text-3xl font-bold text-black mb-4'),
            P('Join over 12,000 European collectors using AI-powered art advisory.',
              cls='text-base text-gray-500 max-w-xl mx-auto mb-8'),
            Div(
                A('Start Advisory Session', href='/app',
                  cls='inline-block px-8 py-3 rounded-full font-semibold text-base no-underline bg-black text-white hover:bg-gray-800 transition-colors'),
                A('Create Account' if login_enabled else 'Open App',
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
            P('Supported by', cls='text-xs text-gray-400 uppercase tracking-wider mb-4'),
            A('Tezos Foundation', href='https://tezos.foundation/', target='_blank',
              cls='text-sm text-gray-500 no-underline hover:text-black transition-colors font-medium'),
            cls='max-w-7xl mx-auto text-center'
        ),
        cls='py-8 px-8 bg-gray-50 border-t border-gray-100'
    )

    return Div(hero, features, how_it_works, agents_preview, stats, cta, partners)
