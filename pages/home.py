from fasthtml.common import *


def home_page():
    hero = Section(
        Div(
            Div(
                H1('Invest in Blue-Chip Art for Long-Term Returns',
                   cls='font-display text-4xl md:text-5xl font-bold leading-tight max-w-3xl mb-6 text-white'),
                P('A members-only platform connecting investors with expertly curated fine art. '
                  'Own fractional shares of museum-quality works by the world\'s most sought-after artists.',
                  cls='text-lg max-w-2xl text-white/90 mb-8 leading-relaxed'),
                Div(
                    Span('\u2713 Asset-backed security',
                         cls='flex items-center gap-2 bg-white/10 border border-white/15 px-4 py-2 rounded-full text-sm text-white'),
                    Span('\u2713 14.1% avg. net return',
                         cls='flex items-center gap-2 bg-white/10 border border-white/15 px-4 py-2 rounded-full text-sm text-white'),
                    Span('\u2713 From $500 minimum',
                         cls='flex items-center gap-2 bg-white/10 border border-white/15 px-4 py-2 rounded-full text-sm text-white'),
                    cls='flex gap-4 mb-8 flex-wrap'
                ),
                Div(
                    A('Start Investing', href='/investors',
                      cls='inline-block px-8 py-3 rounded-md font-semibold text-base no-underline bg-accent text-dark hover:bg-accent-dark transition-colors'),
                    A('Consign Artwork', href='/artists',
                      cls='inline-block px-8 py-3 rounded-md font-semibold text-base no-underline bg-transparent text-white border-2 border-white/30 hover:border-accent hover:text-accent transition-colors'),
                    cls='flex gap-4 flex-wrap'
                ),
                cls='max-w-7xl mx-auto relative z-10'
            ),
            cls='hero-pattern'
        ),
        cls='art-gradient py-24 px-8 relative overflow-hidden'
    )

    stats = Section(
        Div(
            Div(H3('14.1%', cls='text-3xl font-extrabold text-primary mb-1'), P('Avg. Net Return', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
            Div(H3('$48M', cls='text-3xl font-extrabold text-primary mb-1'), P('Investor Distributions', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
            Div(H3('$285M', cls='text-3xl font-extrabold text-primary mb-1'), P('Art Under Management', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
            Div(H3('12,400+', cls='text-3xl font-extrabold text-primary mb-1'), P('Investors', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
            Div(H3('180+', cls='text-3xl font-extrabold text-primary mb-1'), P('Artworks Funded', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
            Div(H3('24', cls='text-3xl font-extrabold text-primary mb-1'), P('Countries', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
            cls='max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-6 gap-8'
        ),
        cls='bg-gallery-warm border-b border-gray-200 py-8 px-8'
    )

    products = Section(
        Div(
            Div(
                H2('Find Your Perfect Investment Strategy',
                   cls='font-display text-3xl font-bold text-gray-900 mb-4'),
                P('Whether you prefer hand-picked masterpieces or automated diversification, we have the right approach.',
                  cls='text-base text-gray-500 max-w-xl mx-auto'),
                cls='text-center mb-12'
            ),
            Div(
                Div(
                    Div('\u26a1', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Auto Invest', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Set your investment preferences once. Our algorithm diversifies across art categories, periods, and price points for optimal portfolio balance.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    A('Learn more \u2192', href='/how-it-works',
                      cls='block mt-4 no-underline font-semibold text-sm text-accent-dark'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100 hover:-translate-y-1 hover:shadow-lg transition-all'
                ),
                Div(
                    Div('\u270b', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Curated Selection', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Hand-pick every artwork. Browse our gallery of vetted pieces with full provenance, condition reports, and market analysis.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    A('View open offerings \u2192', href='/investors',
                      cls='block mt-4 no-underline font-semibold text-sm text-accent-dark'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100 hover:-translate-y-1 hover:shadow-lg transition-all'
                ),
                Div(
                    Div('\u21c4', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Secondary Market', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Trade your shares anytime. Buy or sell fractional positions on our secondary market for added portfolio liquidity.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100 hover:-translate-y-1 hover:shadow-lg transition-all'
                ),
                cls='grid grid-cols-1 md:grid-cols-3 gap-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8 bg-gallery-cream'
    )

    how_it_works = Section(
        Div(
            Div(
                H2('How Does It Work?', cls='font-display text-3xl font-bold text-white mb-4'),
                P('We acquire, securitize, and manage museum-quality artworks on behalf of our investors.',
                  cls='text-base text-gray-300 max-w-xl mx-auto'),
                cls='text-center mb-12'
            ),
            Div(
                Div(
                    H3('Artists & Galleries', cls='text-accent mb-4 text-lg font-bold'),
                    P('Leading artists and galleries consign works through Kanvas.ai for broader collector access '
                      'and upfront capital. Fair market valuations by independent appraisers.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    A('Consign artwork \u2192', href='/artists',
                      cls='block mt-4 text-accent no-underline font-semibold text-sm'),
                    cls='bg-white rounded-xl p-8 shadow-sm border-l-4 border-accent'
                ),
                Div(
                    H3('Kanvas.ai', cls='text-primary mb-4 text-lg font-bold'),
                    P('We handle authentication, insurance, secure storage, and the full investment lifecycle \u2014 '
                      'from acquisition and fractional offering to eventual sale and profit distribution.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border-l-4 border-primary'
                ),
                Div(
                    H3('Investors', cls='text-primary-light mb-4 text-lg font-bold'),
                    P('Join thousands of investors building diversified art portfolios. Earn returns when artworks '
                      'appreciate and are sold. Track your holdings in real-time.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    A('Start investing \u2192', href='/investors',
                      cls='block mt-4 text-primary no-underline font-semibold text-sm'),
                    cls='bg-white rounded-xl p-8 shadow-sm border-l-4 border-primary-light'
                ),
                cls='grid grid-cols-1 md:grid-cols-3 gap-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='bg-dark text-white py-20 px-8'
    )

    security = Section(
        Div(
            Div(
                Div(
                    H2('Asset-Backed Investments',
                       cls='font-display text-3xl mb-4'),
                    P('Every Kanvas.ai offering is backed by a physical artwork, professionally appraised, '
                      'insured, and stored in museum-grade, climate-controlled facilities.',
                      cls='text-lg mb-6'),
                    P('Art has historically shown low correlation to equities and bonds, making it an excellent '
                      'portfolio diversifier. Blue-chip art has appreciated at 13.8% annually over the past 25 years.',
                      cls='text-gray-500 mb-8'),
                    A('Learn about our process', href='/how-it-works',
                      cls='inline-block px-8 py-3 rounded-md font-semibold text-base no-underline bg-primary text-white hover:bg-primary-light transition-colors'),
                ),
                Div(
                    Div(
                        Div(H3('100%', cls='text-3xl font-extrabold text-primary mb-1'), P('Artworks insured & authenticated', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
                        Div(H3('180+', cls='text-3xl font-extrabold text-primary mb-1'), P('Artworks successfully funded', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
                        cls='grid grid-cols-2 gap-8'
                    ),
                    cls='bg-white p-8 rounded-xl shadow-sm'
                ),
                cls='grid grid-cols-1 md:grid-cols-2 gap-16 items-center'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8 bg-gallery-cream'
    )

    cta = Section(
        Div(
            H2('Ready to Invest in Art?',
               cls='font-display text-3xl mb-4'),
            P('Join over 12,000 investors building wealth through blue-chip art.',
              cls='text-lg text-white/90 max-w-xl mx-auto mb-8'),
            Div(
                A('Create Free Account', href='/register',
                  cls='inline-block px-8 py-3 rounded-md font-semibold text-base no-underline bg-accent text-dark hover:bg-accent-dark transition-colors'),
                A('Learn More', href='/how-it-works',
                  cls='inline-block px-8 py-3 rounded-md font-semibold text-base no-underline bg-transparent text-white border-2 border-white/30 hover:border-accent hover:text-accent transition-colors'),
                cls='flex gap-4 flex-wrap justify-center'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='art-gradient text-white py-20 px-8 text-center'
    )

    return Div(hero, stats, products, how_it_works, security, cta)
