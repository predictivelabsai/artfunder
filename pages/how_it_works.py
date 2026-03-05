from fasthtml.common import *


def how_it_works_page():
    hero = Section(
        Div(
            H1('How Kanvas.ai Works', cls='font-display text-4xl font-extrabold text-white mb-4'),
            P('A transparent, secure process connecting art collectors and investors through fractional ownership of museum-quality artworks.',
              cls='text-lg text-white/90 max-w-2xl'),
            cls='max-w-7xl mx-auto relative z-10'
        ),
        cls='art-gradient py-16 px-8'
    )

    def step_item(num, title, desc):
        return Div(
            Div(num, cls='w-12 h-12 min-w-[48px] bg-accent text-dark rounded-full flex items-center justify-center font-extrabold text-lg'),
            Div(
                H3(title, cls='text-lg font-bold mb-2'),
                P(desc, cls='text-gray-500 text-sm'),
            ),
            cls='flex gap-6 mb-10'
        )

    for_investors = Section(
        Div(
            Div(
                H2('For Investors', cls='font-display text-3xl font-bold text-gray-900 mb-4'),
                P('Start building your art portfolio in three simple steps.', cls='text-base text-gray-500 max-w-xl mx-auto'),
                cls='text-center mb-12'
            ),
            step_item('1', 'Create Your Account',
                       'Sign up in minutes and complete a quick verification. Browse our curated gallery of investment-grade artworks with full provenance and condition reports.'),
            step_item('2', 'Choose Your Investment Strategy',
                       'Invest in individual artworks you love, or set up Auto Invest to automatically diversify across categories, periods, and price points. Minimum investment from $500.'),
            step_item('3', 'Earn Returns on Sale',
                       'When an artwork appreciates and is sold, you receive your proportional share of the profits. Track valuations and portfolio performance in real-time through your dashboard.'),
            Div(
                A('Start Investing Now', href='/register',
                  cls='inline-block px-8 py-3 rounded-md font-semibold text-base no-underline bg-primary text-white hover:bg-primary-light transition-colors'),
                cls='text-center mt-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8 bg-gallery-cream'
    )

    for_artists = Section(
        Div(
            Div(
                H2('For Artists & Galleries', cls='font-display text-3xl font-bold text-white mb-4'),
                P('Access a new channel for your works with upfront capital and broader collector reach.', cls='text-base text-gray-300 max-w-xl mx-auto'),
                cls='text-center mb-12'
            ),
            step_item('1', 'Submit Your Artwork',
                       'Tell us about your piece, its provenance, exhibition history, and your valuation expectations. We review submissions within 48 hours.'),
            step_item('2', 'Authentication & Appraisal',
                       'Our team of art experts conducts thorough authentication, condition assessment, and independent market valuation. We work with leading appraisers and art historians.'),
            step_item('3', 'Receive Capital',
                       'Once approved and funded by our investor community, you receive upfront payment. The artwork is securely stored and insured while our investors hold fractional shares.'),
            Div(
                A('Consign Artwork', href='/artists',
                  cls='inline-block px-8 py-3 rounded-md font-semibold text-base no-underline bg-accent text-dark hover:bg-accent-dark transition-colors'),
                cls='text-center mt-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='bg-dark text-white py-20 px-8'
    )

    offering_types = Section(
        Div(
            Div(
                H2('What We Offer', cls='font-display text-3xl font-bold text-gray-900 mb-4'),
                P('Multiple ways to invest in the art market.', cls='text-base text-gray-500 max-w-xl mx-auto'),
                cls='text-center mb-12'
            ),
            Div(
                Div(
                    Div('\U0001f3a8', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Fractional Ownership', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Own shares of individual blue-chip artworks. Benefit from appreciation when the piece is sold. Typical hold periods: 3-10 years.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100 hover:-translate-y-1 hover:shadow-lg transition-all'
                ),
                Div(
                    Div('\U0001f4a1', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Art-Backed Lending', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Fund loans secured against high-value art collections. Fixed returns with the artwork as collateral. Terms: 12-36 months.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100 hover:-translate-y-1 hover:shadow-lg transition-all'
                ),
                Div(
                    Div('\U0001f30d', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Gallery Financing', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Provide capital to galleries for acquisitions and exhibitions. Returns tied to gallery sales performance. Terms: 6-24 months.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100 hover:-translate-y-1 hover:shadow-lg transition-all'
                ),
                cls='grid grid-cols-1 md:grid-cols-3 gap-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8 bg-gallery-cream'
    )

    risk = Section(
        Div(
            Div(
                H2('Risk Management', cls='font-display text-3xl font-bold text-white mb-4'),
                P('How we protect your investments.', cls='text-base text-gray-300 max-w-xl mx-auto'),
                cls='text-center mb-12'
            ),
            Div(
                Div(
                    H3('Physical Asset Security', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Every artwork is stored in museum-grade, climate-controlled facilities with 24/7 security, full insurance coverage, and regular condition monitoring.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    H3('Expert Authentication', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('All artworks undergo rigorous authentication by leading experts. We verify provenance, examine condition, and confirm attribution before any offering.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    H3('Independent Appraisal', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Fair market valuations by certified, independent appraisers using auction records, private sale comparables, and current market conditions.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    H3('Diversification', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Spread risk across multiple artworks, artists, periods, and categories. Art has historically shown low correlation to traditional financial markets.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                cls='grid grid-cols-1 md:grid-cols-2 gap-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='bg-dark text-white py-20 px-8'
    )

    return Div(hero, for_investors, for_artists, offering_types, risk)
