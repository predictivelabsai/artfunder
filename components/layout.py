from fasthtml.common import *


def app_styles():
    """Tailwind CDN with clean white minimal + black aesthetic."""
    return (
        Link(rel='icon', href='/static/favicon.ico', type='image/x-icon'),
        Link(rel='stylesheet', href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Cormorant+Garamond:wght@400;500;600;700&display=swap'),
        Script(src='https://cdn.tailwindcss.com'),
        Script("""
        tailwind.config = {
          theme: {
            extend: {
              colors: {
                ink: { DEFAULT: '#1A1A1A', muted: '#6B7280', dim: '#9CA3AF' },
                surface: { DEFAULT: '#FFFFFF', alt: '#F5F5F5' },
                border: '#E5E5E5',
              },
              fontFamily: {
                display: ['Cormorant Garamond', 'Georgia', 'serif'],
                sans: ['Inter', 'system-ui', 'sans-serif'],
              },
            },
          },
        }
        """),
        Style("""
        body { font-family: 'Inter', system-ui, sans-serif; }
        """),
    )


def NavBar(active='home', sess=None):
    from utils.config import settings
    login_enabled = settings().login_enabled

    logged_in = sess and sess.get('auth') if login_enabled else False
    user_name = (sess.get('name', '') if sess else '') or ''

    nav_items_left = [
        ('home', '/', 'Home'),
        ('advisory', '/app', 'Advisory'),
        ('investors', '/investors', 'Collection'),
        ('artists', '/artists', 'Artists'),
        ('about', '/about', 'About'),
    ]
    nav_items_right = [
        ('art-index', 'https://artindex.kanvas.ai/', 'Art Index'),
        ('contact', '/contact', 'Contact'),
    ]

    def nav_link(key, href, label):
        base = 'text-sm font-medium no-underline transition-colors duration-200'
        if key == active:
            return A(label, href=href, cls=f'{base} text-black')
        return A(label, href=href, cls=f'{base} text-gray-400 hover:text-black')

    if not login_enabled:
        auth_items = [
            Li(A('Open App', href='/app',
                 cls='bg-black text-white px-5 py-2 rounded-full font-semibold text-sm no-underline hover:bg-gray-800 transition-colors')),
        ]
    elif logged_in:
        auth_items = [
            Li(Span(user_name, cls='text-gray-400 text-sm')) if user_name else '',
            Li(A('Log Out', href='/logout',
                 cls='bg-black text-white px-5 py-2 rounded-full font-semibold text-sm no-underline hover:bg-gray-800 transition-colors')),
        ]
    else:
        auth_items = [
            Li(A('Login', href='/login',
                 cls='bg-black text-white px-5 py-2 rounded-full font-semibold text-sm no-underline hover:bg-gray-800 transition-colors')),
        ]

    return Nav(
        Div(
            A('Kanvas', Span('.ai', cls='text-gray-400'), href='/',
              cls='font-display text-2xl font-bold text-black no-underline tracking-wide shrink-0'),
            Button('☰',
                   cls='md:hidden bg-transparent border-none text-black text-2xl cursor-pointer',
                   onclick="document.getElementById('nav-links').classList.toggle('hidden')"),
            Ul(
                *[Li(nav_link(key, href, label)) for key, href, label in nav_items_left],
                Li(cls='flex-grow'),
                *[Li(nav_link(key, href, label)) for key, href, label in nav_items_right],
                *auth_items,
                id='nav-links',
                cls='hidden md:flex items-center gap-8 list-none m-0 p-0 flex-grow'
            ),
            cls='max-w-7xl mx-auto flex items-center justify-between h-[70px] gap-8'
        ),
        cls='bg-white px-8 sticky top-0 z-50 border-b border-gray-100'
    )


def PageFooter():
    from fasthtml.components import Footer as FooterTag
    return FooterTag(
        Div(
            Div(
                Div(
                    H3('Kanvas', Span('.ai', cls='text-gray-500'),
                       cls='font-display text-black text-xl mb-4 tracking-wide'),
                    P('AI-powered art advisory and investment platform. We connect collectors with expertly '
                      'curated artworks, market intelligence, and fractional ownership opportunities.',
                      cls='text-sm leading-relaxed text-gray-500'),
                ),
                Div(
                    H4('Platform', cls='text-black text-sm uppercase tracking-wider mb-4'),
                    Ul(
                        Li(A('Advisory', href='/app', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A('Collection', href='/investors', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A('For Artists', href='/artists', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A('Analytics', href='/app/analytics', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                Div(
                    H4('Resources', cls='text-black text-sm uppercase tracking-wider mb-4'),
                    Ul(
                        Li(A('Art Index', href='https://artindex.kanvas.ai/', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A('About', href='/about', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A('Contact', href='/contact', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                Div(
                    H4('Legal', cls='text-black text-sm uppercase tracking-wider mb-4'),
                    Ul(
                        Li(A('Terms of Service', href='/terms', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A('Privacy Policy', href='/privacy', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A('Risk Disclosures', href='/risk', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                cls='max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12'
            ),
            Div(
                P('© 2026 Kanvas.ai. All rights reserved.'),
                P('Art advisory and investment involve risk. Past performance does not guarantee future results.'),
                cls='max-w-7xl mx-auto mt-12 pt-8 border-t border-gray-200 flex flex-col md:flex-row justify-between items-center text-sm gap-4'
            ),
        ),
        cls='bg-white text-gray-400 pt-16 pb-8 px-8 border-t border-gray-100'
    )


def Page(content, active='home', title='Kanvas.ai', sess=None):
    return (
        Title(f'{title} - AI Art Advisory & Investment'),
        NavBar(active, sess=sess),
        Main(content),
        PageFooter()
    )
