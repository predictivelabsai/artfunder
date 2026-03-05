from fasthtml.common import *


def app_styles():
    """Tailwind CDN with clean light blue gallery aesthetic."""
    return (
        # Favicon
        Link(rel='icon', href='/static/favicon.ico', type='image/x-icon'),
        # Google Fonts
        Link(rel='stylesheet', href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Cormorant+Garamond:wght@400;500;600;700&display=swap'),
        # Tailwind CDN
        Script(src='https://cdn.tailwindcss.com'),
        Script("""
        tailwind.config = {
          theme: {
            extend: {
              colors: {
                primary: { DEFAULT: '#2563EB', dark: '#1E40AF', light: '#3B82F6' },
                accent: { DEFAULT: '#C9A84C', dark: '#B8933A', light: '#D4B96A' },
                dark: { DEFAULT: '#1E40AF', deeper: '#1E3A8A' },
                gallery: { DEFAULT: '#EFF6FF', warm: '#F0F9FF', cream: '#FFFFFF' },
              },
              fontFamily: {
                display: ['Cormorant Garamond', 'Georgia', 'serif'],
                sans: ['Inter', 'system-ui', 'sans-serif'],
              },
            },
          },
        }
        """),
        # Minimal custom styles
        Style("""
        body { font-family: 'Inter', system-ui, sans-serif; }
        .art-gradient { background: linear-gradient(135deg, #1E40AF 0%, #2563EB 50%, #3B82F6 100%); }
        """),
    )


def NavBar(active='home', sess=None):
    logged_in = sess and sess.get('auth')
    user_name = (sess.get('name', '') if sess else '') or ''

    nav_items_left = [
        ('home', '/', 'Home'),
        ('investors', '/investors', 'Investors'),
        ('artists', '/artists', 'Artists'),
        ('about', '/about', 'About'),
        ('contact', '/contact', 'Contact'),
    ]
    nav_items_right = [
        ('art-index', 'https://artindex.kanvas.ai/', 'Art Index'),
        ('how-it-works', '/how-it-works', 'How It Works'),
    ]

    def nav_link(key, href, label):
        base = 'text-sm font-medium no-underline transition-colors duration-200'
        if key == active:
            return A(label, href=href, cls=f'{base} text-white')
        return A(label, href=href, cls=f'{base} text-blue-100 hover:text-white')

    if logged_in:
        auth_items = [
            Li(Span(user_name, cls='text-blue-200 text-sm')) if user_name else '',
            Li(A('Log Out', href='/logout',
                 cls='bg-white/15 text-white px-5 py-2 rounded-full font-semibold text-sm no-underline hover:bg-white/25 transition-colors')),
        ]
    else:
        auth_items = [
            Li(A('Login', href='/login',
                 cls='bg-white text-primary px-5 py-2 rounded-full font-semibold text-sm no-underline hover:bg-blue-50 transition-colors')),
        ]

    return Nav(
        Div(
            A('Kanvas', Span('.ai', cls='text-blue-200'), href='/',
              cls='font-display text-2xl font-bold text-white no-underline tracking-wide shrink-0'),
            Button('\u2630',
                   cls='md:hidden bg-transparent border-none text-white text-2xl cursor-pointer',
                   onclick="document.getElementById('nav-links').classList.toggle('hidden')"),
            Ul(
                *[Li(nav_link(key, href, label)) for key, href, label in nav_items_left],
                Li(cls='flex-grow'),  # spacer pushes right items
                *[Li(nav_link(key, href, label)) for key, href, label in nav_items_right],
                *auth_items,
                id='nav-links',
                cls='hidden md:flex items-center gap-8 list-none m-0 p-0 flex-grow'
            ),
            cls='max-w-7xl mx-auto flex items-center justify-between h-[70px] gap-8'
        ),
        cls='bg-primary px-8 sticky top-0 z-50 border-b border-white/15'
    )


def PageFooter():
    from fasthtml.components import Footer as FooterTag
    return FooterTag(
        Div(
            Div(
                Div(
                    H3('Kanvas', Span('.ai', cls='text-blue-200'),
                       cls='font-display text-white text-xl mb-4 tracking-wide'),
                    P('Fine art investment made accessible. We connect investors with expertly curated artworks, '
                      'delivering transparent returns backed by tangible, appreciating assets.',
                      cls='text-sm leading-relaxed text-blue-200'),
                ),
                Div(
                    H4('Platform', cls='text-white text-sm uppercase tracking-wider mb-4'),
                    Ul(
                        Li(A('How It Works', href='/how-it-works', cls='text-blue-300 no-underline text-sm hover:text-white transition-colors'), cls='mb-2'),
                        Li(A('Open Investments', href='/investors', cls='text-blue-300 no-underline text-sm hover:text-white transition-colors'), cls='mb-2'),
                        Li(A('For Artists', href='/artists', cls='text-blue-300 no-underline text-sm hover:text-white transition-colors'), cls='mb-2'),
                        Li(A('About Us', href='/about', cls='text-blue-300 no-underline text-sm hover:text-white transition-colors'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                Div(
                    H4('Resources', cls='text-white text-sm uppercase tracking-wider mb-4'),
                    Ul(
                        Li(A('FAQ', href='/faq', cls='text-blue-300 no-underline text-sm hover:text-white transition-colors'), cls='mb-2'),
                        Li(A('Risk Statement', href='/risk', cls='text-blue-300 no-underline text-sm hover:text-white transition-colors'), cls='mb-2'),
                        Li(A('Contact', href='/contact', cls='text-blue-300 no-underline text-sm hover:text-white transition-colors'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                Div(
                    H4('Legal', cls='text-white text-sm uppercase tracking-wider mb-4'),
                    Ul(
                        Li(A('Terms of Service', href='/terms', cls='text-blue-300 no-underline text-sm hover:text-white transition-colors'), cls='mb-2'),
                        Li(A('Privacy Policy', href='/privacy', cls='text-blue-300 no-underline text-sm hover:text-white transition-colors'), cls='mb-2'),
                        Li(A('Risk Disclosures', href='/risk', cls='text-blue-300 no-underline text-sm hover:text-white transition-colors'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                cls='max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12'
            ),
            Div(
                P('\u00a9 2026 Kanvas.ai. All rights reserved. Investing involves risk and can result in loss of capital.'),
                P('All investments are backed by physical artworks held in secure, climate-controlled storage.'),
                cls='max-w-7xl mx-auto mt-12 pt-8 border-t border-white/15 flex flex-col md:flex-row justify-between items-center text-sm gap-4'
            ),
        ),
        cls='bg-primary-dark text-blue-200 pt-16 pb-8 px-8'
    )


def Page(content, active='home', title='Kanvas.ai', sess=None):
    return (
        Title(f'{title} - Fine Art Investment Platform'),
        NavBar(active, sess=sess),
        Main(content),
        PageFooter()
    )
