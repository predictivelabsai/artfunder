from fasthtml.common import *


def artists_page():
    hero = Section(
        Div(
            H1('Consign Your Art. Reach New Collectors.', cls='font-display text-4xl font-extrabold text-white mb-4'),
            P('Access upfront capital and a global investor base for your artworks \u2014 a new channel for artists and galleries seeking liquidity and exposure.',
              cls='text-lg text-white/90 max-w-2xl mb-8'),
            Div(
                A('Submit Artwork', href='/contact',
                  cls='inline-block px-8 py-3 rounded-md font-semibold text-base no-underline bg-accent text-dark hover:bg-accent-dark transition-colors'),
                cls='flex gap-4 flex-wrap'
            ),
            cls='max-w-7xl mx-auto relative z-10'
        ),
        cls='art-gradient py-16 px-8'
    )

    benefits = Section(
        Div(
            Div(
                H2('Why Consign With Kanvas.ai', cls='font-display text-3xl font-bold text-gray-900 mb-4'),
                P('We help artists and galleries unlock the value of their collections.', cls='text-base text-gray-500 max-w-xl mx-auto'),
                cls='text-center mb-12'
            ),
            Div(
                Div(
                    Div('\u23f1\ufe0f', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Upfront Capital', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Receive payment when your artwork is funded by our investor community. No waiting for auction results or gallery sales cycles.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100 hover:-translate-y-1 hover:shadow-lg transition-all'
                ),
                Div(
                    Div('\U0001f30d', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Global Exposure', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Your work is presented to over 12,000 investors across 24 countries. Build awareness and collector interest beyond traditional gallery channels.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100 hover:-translate-y-1 hover:shadow-lg transition-all'
                ),
                Div(
                    Div('\U0001f50d', cls='w-12 h-12 bg-gradient-to-br from-primary to-primary-light rounded-xl flex items-center justify-center mb-5 text-2xl text-white'),
                    H3('Fair Valuation', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Independent appraisals using auction records and market comparables. Transparent pricing ensures fair value for your work.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100 hover:-translate-y-1 hover:shadow-lg transition-all'
                ),
                cls='grid grid-cols-1 md:grid-cols-3 gap-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8 bg-gallery-cream'
    )

    eligible = Section(
        Div(
            Div(
                H2('What We Accept', cls='font-display text-3xl font-bold text-white mb-4'),
                P('We consider a wide range of fine art categories.', cls='text-base text-gray-300 max-w-xl mx-auto'),
                cls='text-center mb-12'
            ),
            Div(
                Div(
                    H3('Paintings', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Oil, acrylic, watercolor, and mixed media paintings by established and emerging artists with strong auction records or gallery representation.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    H3('Sculpture', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Three-dimensional works in bronze, marble, steel, and contemporary materials from artists with recognized exhibition histories.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    H3('Photography', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Limited edition fine art photography from established photographers. Editions must be documented and authenticated.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                Div(
                    H3('Prints & Editions', cls='text-lg font-bold text-gray-900 mb-3'),
                    P('Screen prints, lithographs, etchings, and other limited editions from artists with strong secondary market demand.',
                      cls='text-gray-500 text-sm leading-relaxed'),
                    cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
                ),
                cls='grid grid-cols-1 md:grid-cols-2 gap-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='bg-dark text-white py-20 px-8'
    )

    deal_details = Section(
        Div(
            Div(
                H2('Consignment Details', cls='font-display text-3xl font-bold text-gray-900 mb-4'),
                cls='text-center mb-12'
            ),
            Div(
                Div(H3('$10K - $10M', cls='text-3xl font-extrabold text-primary mb-1'), P('Artwork Value Range', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
                Div(H3('3 - 10 yr', cls='text-3xl font-extrabold text-primary mb-1'), P('Typical Hold Period', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
                Div(H3('180+', cls='text-3xl font-extrabold text-primary mb-1'), P('Works Consigned', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
                Div(H3('48 hrs', cls='text-3xl font-extrabold text-primary mb-1'), P('Initial Review', cls='text-xs text-gray-500 uppercase tracking-wider'), cls='text-center'),
                cls='max-w-7xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8 bg-gallery-cream'
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

    process = Section(
        Div(
            Div(
                H2('Consignment Process', cls='font-display text-3xl font-bold text-gray-900 mb-4'),
                cls='text-center mb-12'
            ),
            step_item('1', 'Submit Your Work',
                       'Fill out our online form with details about the artwork, its provenance, exhibition history, and your valuation expectations.'),
            step_item('2', 'Authentication & Appraisal',
                       'Our team of art experts verifies authenticity, examines condition, and commissions independent market valuation using auction and private sale comparables.'),
            step_item('3', 'Offering Goes Live',
                       'Your artwork is listed on the platform for fractional investment. Professional photography and detailed descriptions accompany every offering.'),
            step_item('4', 'Receive Payment',
                       'Once fully funded by our investor community, you receive payment. The artwork is transferred to our secure, climate-controlled storage facilities.'),
            Div(
                A('Submit Artwork', href='/contact',
                  cls='inline-block px-8 py-3 rounded-md font-semibold text-base no-underline bg-primary text-white hover:bg-primary-light transition-colors'),
                cls='text-center mt-8'
            ),
            cls='max-w-7xl mx-auto'
        ),
        cls='py-20 px-8'
    )

    return Div(hero, benefits, eligible, deal_details, process)
