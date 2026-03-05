from fasthtml.common import *


def contact_page():
    hero = Section(
        Div(
            H1('Contact Us', cls='font-display text-4xl font-extrabold text-white mb-4'),
            P('Get in touch with our team. We are here to help with any questions about investing or consigning through Kanvas.ai.',
              cls='text-lg text-white/90 max-w-2xl'),
            cls='max-w-7xl mx-auto relative z-10'
        ),
        cls='art-gradient py-16 px-8'
    )

    offices = Section(
        Div(
            Div(
                H2('Our Offices', cls='font-display text-3xl font-bold text-gray-900 mb-4'),
                cls='text-center mb-12'
            ),
            Div(
                Div(
                    H3('New York (HQ)', cls='text-lg font-bold text-gray-900 mb-3'),
                    P(Strong('Address'), Br(),
                      '520 West 25th Street', Br(),
                      'Suite 300', Br(),
                      'New York, NY 10001', Br(),
                      'United States', cls='mb-4 text-sm text-gray-600 leading-relaxed'),
                    P(Strong('Email'), Br(),
                      A('nyc@kanvas.ai', href='mailto:nyc@kanvas.ai',
                        cls='text-primary no-underline'), cls='mb-4 text-sm'),
                    P(Strong('Phone'), Br(),
                      A('+1 212 555 0198', href='tel:+12125550198',
                        cls='text-primary no-underline'), cls='text-sm'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    H3('London', cls='text-lg font-bold text-gray-900 mb-3'),
                    P(Strong('Address'), Br(),
                      '12 Mason\'s Yard', Br(),
                      'St James\'s', Br(),
                      'London SW1Y 6BU', Br(),
                      'United Kingdom', cls='mb-4 text-sm text-gray-600 leading-relaxed'),
                    P(Strong('Email'), Br(),
                      A('london@kanvas.ai', href='mailto:london@kanvas.ai',
                        cls='text-primary no-underline'), cls='mb-4 text-sm'),
                    P(Strong('Phone'), Br(),
                      A('+44 20 7123 4567', href='tel:+442071234567',
                        cls='text-primary no-underline'), cls='text-sm'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    H3('Hong Kong', cls='text-lg font-bold text-gray-900 mb-3'),
                    P(Strong('Address'), Br(),
                      '50 Connaught Road Central', Br(),
                      'Central, Hong Kong', cls='mb-4 text-sm text-gray-600 leading-relaxed'),
                    P(Strong('Email'), Br(),
                      A('hk@kanvas.ai', href='mailto:hk@kanvas.ai',
                        cls='text-primary no-underline'), cls='mb-4 text-sm'),
                    P(Strong('Phone'), Br(),
                      A('+852 3456 7890', href='tel:+85234567890',
                        cls='text-primary no-underline'), cls='text-sm'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                cls='grid grid-cols-1 md:grid-cols-3 gap-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8 bg-gallery-cream'
    )

    general = Section(
        Div(
            Div(
                H2('General Enquiries', cls='font-display text-3xl font-bold text-white mb-4'),
                cls='text-center mb-12'
            ),
            Div(
                Div(
                    H3('Investor Support', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Questions about your account, investments, or portfolio?', cls='text-gray-500 text-sm mb-4'),
                    P(A('investors@kanvas.ai', href='mailto:investors@kanvas.ai',
                        cls='text-accent no-underline font-semibold')),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    H3('Consignment Enquiries', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Want to consign artwork or have questions about the process?', cls='text-gray-500 text-sm mb-4'),
                    P(A('consign@kanvas.ai', href='mailto:consign@kanvas.ai',
                        cls='text-accent no-underline font-semibold')),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    H3('Press & Media', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Media enquiries, partnership opportunities, or press information?', cls='text-gray-500 text-sm mb-4'),
                    P(A('press@kanvas.ai', href='mailto:press@kanvas.ai',
                        cls='text-accent no-underline font-semibold')),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                cls='grid grid-cols-1 md:grid-cols-3 gap-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='bg-dark text-white py-20 px-8'
    )

    return Div(hero, offices, general)
