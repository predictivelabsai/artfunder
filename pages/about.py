from fasthtml.common import *


def about_page():
    hero = Section(
        Div(
            H1('About Kanvas.ai', cls='font-display text-4xl font-extrabold text-white mb-4'),
            P('We are democratizing art investment \u2014 making fine art ownership '
              'accessible, transparent, and rewarding for everyone.',
              cls='text-lg text-white/90 max-w-2xl'),
            cls='max-w-7xl mx-auto relative z-10'
        ),
        cls='art-gradient py-16 px-8'
    )

    mission = Section(
        Div(
            Div(
                Div(
                    H2('Our Mission', cls='font-display text-3xl mb-6'),
                    P('Kanvas.ai was founded with a simple belief: art investment should not be '
                      'reserved for billionaires and institutions. By leveraging technology and fractional ownership, '
                      'we connect everyday investors with museum-quality artworks, creating '
                      'value for both investors and the art community.',
                      cls='text-base leading-relaxed mb-6'),
                    P('Our platform enables investors to build diversified art portfolios '
                      'backed by physical, appreciating assets, while giving artists and galleries access to a '
                      'global community of collectors and upfront capital for their works.',
                      cls='text-base leading-relaxed text-gray-500'),
                ),
                Div(
                    Div(
                        Div(H3('2023', cls='text-3xl font-extrabold text-primary mb-1'), P('Founded', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
                        Div(H3('45+', cls='text-3xl font-extrabold text-primary mb-1'), P('Team Members', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
                        Div(H3('24', cls='text-3xl font-extrabold text-primary mb-1'), P('Countries', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
                        Div(H3('$285M', cls='text-3xl font-extrabold text-primary mb-1'), P('Art Under Management', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
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

    values = Section(
        Div(
            Div(
                H2('Our Values', cls='font-display text-3xl font-bold text-white mb-4'),
                P('The principles that guide everything we do.', cls='text-base text-gray-300 max-w-xl mx-auto'),
                cls='text-center mb-12'
            ),
            Div(
                Div(
                    Div('\U0001f50d', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Transparency', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Full disclosure on every offering. Investors see detailed provenance, condition reports, independent appraisals, and market analysis before investing.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    Div('\U0001f91d', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Trust & Integrity', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('We build long-term relationships through trust, integrity, and rigorous authentication. Every artwork is verified by leading experts before listing.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    Div('\U0001f3a8', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Passion for Art', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('We are collectors, curators, and art lovers. Our team includes art historians, appraisers, and market specialists who live and breathe the art world.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                cls='grid grid-cols-1 md:grid-cols-3 gap-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='bg-dark text-white py-20 px-8'
    )

    presence = Section(
        Div(
            Div(
                H2('Our Presence', cls='font-display text-3xl font-bold text-gray-900 mb-4'),
                P('Operating across key art markets with a growing global footprint.', cls='text-base text-gray-500 max-w-xl mx-auto'),
                cls='text-center mb-12'
            ),
            Div(
                Div(
                    H3('Headquarters', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('New York City, USA', cls='text-gray-900 mb-1'),
                    P('Our main office near the Chelsea gallery district.', cls='text-gray-500 text-sm'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    H3('Europe', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('London, United Kingdom', cls='text-gray-900 mb-1'),
                    P('Serving the European art market and international collectors.', cls='text-gray-500 text-sm'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    H3('Asia-Pacific', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Hong Kong', cls='text-gray-900 mb-1'),
                    P('Our APAC hub covering the rapidly growing Asian art market.', cls='text-gray-500 text-sm'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                cls='grid grid-cols-1 md:grid-cols-3 gap-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8 bg-gallery-cream'
    )

    cta = Section(
        Div(
            H2('Join the Kanvas.ai Community', cls='font-display text-3xl mb-4'),
            P('Whether you are an investor looking to build an art portfolio or an artist seeking new collectors, we are here to help.',
              cls='text-lg text-white/90 max-w-xl mx-auto mb-8'),
            Div(
                A('Start Investing', href='/investors',
                  cls='inline-block px-8 py-3 rounded-md font-semibold text-base no-underline bg-accent text-dark hover:bg-accent-dark transition-colors'),
                A('Consign Artwork', href='/artists',
                  cls='inline-block px-8 py-3 rounded-md font-semibold text-base no-underline bg-transparent text-white border-2 border-white/30 hover:border-accent hover:text-accent transition-colors'),
                cls='flex gap-4 flex-wrap justify-center'
            ),
        ),
        cls='art-gradient text-white py-20 px-8 text-center'
    )

    return Div(hero, mission, values, presence, cta)
