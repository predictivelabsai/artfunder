from fasthtml.common import *


def investors_page():
    hero = Section(
        Div(
            H1('Invest in Fine Art', cls='font-display text-4xl font-extrabold text-white mb-4'),
            P('Own fractional shares of blue-chip artworks by the world\'s most sought-after artists. '
              'Diversify your portfolio with an asset class that has outperformed the S&P 500 over the past 25 years.',
              cls='text-lg text-white/90 max-w-2xl'),
            cls='max-w-7xl mx-auto relative z-10'
        ),
        cls='art-gradient py-16 px-8'
    )

    benefits = Section(
        Div(
            Div(
                H2('Why Invest With Kanvas.ai', cls='font-display text-3xl font-bold text-gray-900 mb-4'),
                P('Tangible, appreciating assets with institutional-grade security.', cls='text-base text-gray-500 max-w-xl mx-auto'),
                cls='text-center mb-12'
            ),
            Div(
                Div(
                    Div('\U0001f4c8', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Strong Historical Returns', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Blue-chip art has appreciated at 13.8% annually over the past 25 years. Our curated offerings target 10-18% annualized returns.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100 hover:-translate-y-1 hover:shadow-lg transition-all'
                ),
                Div(
                    Div('\U0001f3a8', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Physical Asset Security', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Every investment is backed by a real artwork, professionally appraised, fully insured, and stored in museum-grade facilities.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100 hover:-translate-y-1 hover:shadow-lg transition-all'
                ),
                Div(
                    Div('\U0001f4ca', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Portfolio Diversification', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Art shows low correlation to stocks and bonds. Add an uncorrelated asset class to reduce overall portfolio volatility.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100 hover:-translate-y-1 hover:shadow-lg transition-all'
                ),
                cls='grid grid-cols-1 md:grid-cols-3 gap-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8 bg-gallery-cream'
    )

    investment_options = Section(
        Div(
            Div(
                H2('Investment Options', cls='font-display text-3xl font-bold text-white mb-4'),
                P('Choose the approach that suits your style.', cls='text-base text-gray-300 max-w-xl mx-auto'),
                cls='text-center mb-12'
            ),
            Div(
                Div(
                    H3('Auto Invest', cls='text-accent mb-4 text-lg font-bold'),
                    P('Set your criteria and let our algorithm build your art portfolio.', cls='mb-6 text-gray-500 text-sm'),
                    Div(
                        P('\u2713 Automated portfolio diversification', cls='mb-2 text-sm text-gray-500'),
                        P('\u2713 Custom risk and category preferences', cls='mb-2 text-sm text-gray-500'),
                        P('\u2713 Spread across artists and periods', cls='mb-2 text-sm text-gray-500'),
                        P('\u2713 Reinvestment of sale proceeds', cls='mb-2 text-sm text-gray-500'),
                    ),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    H3('Curated Selection', cls='text-primary mb-4 text-lg font-bold'),
                    P('Browse and select individual artworks from our gallery.', cls='mb-6 text-gray-500 text-sm'),
                    Div(
                        P('\u2713 Full control over your collection', cls='mb-2 text-sm text-gray-500'),
                        P('\u2713 Detailed provenance and appraisals', cls='mb-2 text-sm text-gray-500'),
                        P('\u2713 Choose by artist, period, medium', cls='mb-2 text-sm text-gray-500'),
                        P('\u2713 Real-time valuation tracking', cls='mb-2 text-sm text-gray-500'),
                    ),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    H3('Secondary Market', cls='text-primary-light mb-4 text-lg font-bold'),
                    P('Buy and sell existing fractional positions.', cls='mb-6 text-gray-500 text-sm'),
                    Div(
                        P('\u2713 Added liquidity for your holdings', cls='mb-2 text-sm text-gray-500'),
                        P('\u2713 Access seasoned investments', cls='mb-2 text-sm text-gray-500'),
                        P('\u2713 Adjust portfolio anytime', cls='mb-2 text-sm text-gray-500'),
                        P('\u2713 Market-driven pricing', cls='mb-2 text-sm text-gray-500'),
                    ),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                cls='grid grid-cols-1 md:grid-cols-3 gap-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='bg-dark text-white py-20 px-8'
    )

    key_figures = Section(
        Div(
            Div(
                H2('Investment at a Glance', cls='font-display text-3xl font-bold text-gray-900 mb-4'),
                cls='text-center mb-12'
            ),
            Div(
                Div(H3('$500', cls='text-3xl font-extrabold text-primary mb-1'), P('Minimum Investment', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
                Div(H3('10-18%', cls='text-3xl font-extrabold text-primary mb-1'), P('Target Returns', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
                Div(H3('3-10 yr', cls='text-3xl font-extrabold text-primary mb-1'), P('Hold Period', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
                Div(H3('180+', cls='text-3xl font-extrabold text-primary mb-1'), P('Artworks Funded', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
                cls='max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8 bg-gallery-cream'
    )

    cta = Section(
        Div(
            H2('Start Building Your Art Portfolio', cls='font-display text-3xl mb-4'),
            P('Create your free account and invest in your first artwork in minutes.',
              cls='text-lg text-white/90 max-w-xl mx-auto mb-8'),
            A('Create Account', href='/register',
              cls='inline-block px-8 py-3 rounded-md font-semibold text-base no-underline bg-accent text-dark hover:bg-accent-dark transition-colors'),
        ),
        cls='art-gradient text-white py-20 px-8 text-center'
    )

    return Div(hero, benefits, investment_options, key_figures, cta)
