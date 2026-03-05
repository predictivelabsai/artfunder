from fasthtml.common import *


def app_styles():
    """Tailwind CDN with custom config + minimal custom styles for art gallery aesthetic."""
    return (
        # Google Fonts
        Link(rel='stylesheet', href='https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Cormorant+Garamond:wght@400;500;600;700&display=swap'),
        # Tailwind CDN
        Script(src='https://cdn.tailwindcss.com'),
        Script("""
        tailwind.config = {
          theme: {
            extend: {
              colors: {
                primary: { DEFAULT: '#1A1A2E', dark: '#0F0F1A', light: '#2D2D4E' },
                accent: { DEFAULT: '#C9A84C', dark: '#B8933A', light: '#D4B96A' },
                dark: { DEFAULT: '#0A0A14', deeper: '#050510' },
                gallery: { DEFAULT: '#F5F0E8', warm: '#FAF7F2', cream: '#FFFDF8' },
              },
              fontFamily: {
                display: ['Cormorant Garamond', 'Georgia', 'serif'],
                sans: ['Inter', 'system-ui', 'sans-serif'],
              },
            },
          },
        }
        """),
        # Minimal custom styles for things Tailwind CDN can't easily do
        Style("""
        body { font-family: 'Inter', system-ui, sans-serif; }
        .hero-pattern { background-image: url("data:image/svg+xml,%3Csvg width='80' height='80' viewBox='0 0 80 80' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23C9A84C' fill-opacity='0.03'%3E%3Cpath d='M40 0L80 40L40 80L0 40z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E"); }
        .art-gradient { background: linear-gradient(135deg, #0A0A14 0%, #1A1A2E 40%, #2D2D4E 100%); }
        """),
    )


def NavBar(active='home'):
    nav_items = [
        ('home', '/', 'Home'),
        ('how-it-works', '/how-it-works', 'How It Works'),
        ('investors', '/investors', 'Investors'),
        ('artists', '/artists', 'Artists'),
        ('about', '/about', 'About'),
        ('contact', '/contact', 'Contact'),
    ]

    def nav_link(key, href, label):
        base = 'text-sm font-medium no-underline transition-colors duration-200'
        if key == active:
            return A(label, href=href, cls=f'{base} text-accent')
        return A(label, href=href, cls=f'{base} text-gray-400 hover:text-accent')

    return Nav(
        Div(
            A('Kanvas', Span('.ai', cls='text-accent'), href='/',
              cls='font-display text-2xl font-bold text-white no-underline tracking-wide'),
            Button('\u2630',
                   cls='md:hidden bg-transparent border-none text-white text-2xl cursor-pointer',
                   onclick="document.getElementById('nav-links').classList.toggle('hidden')"),
            Ul(
                *[Li(nav_link(key, href, label)) for key, href, label in nav_items],
                Li(A('Login', href='/login',
                     cls='bg-accent/20 text-accent border border-accent/30 px-5 py-2.5 rounded-md font-semibold text-sm no-underline hover:bg-accent hover:text-dark transition-colors')),
                id='nav-links',
                cls='hidden md:flex items-center gap-8 list-none'
            ),
            cls='max-w-7xl mx-auto flex items-center justify-between h-[70px]'
        ),
        cls='bg-dark px-8 sticky top-0 z-50 shadow-md border-b border-white/5'
    )


def PageFooter():
    from fasthtml.components import Footer as FooterTag
    return FooterTag(
        Div(
            Div(
                Div(
                    H3('Kanvas', Span('.ai', cls='text-accent'),
                       cls='font-display text-white text-xl mb-4 tracking-wide'),
                    P('Fine art investment made accessible. We connect investors with expertly curated artworks, '
                      'delivering transparent returns backed by tangible, appreciating assets.',
                      cls='text-sm leading-relaxed text-gray-400'),
                ),
                Div(
                    H4('Platform', cls='text-white text-sm uppercase tracking-wider mb-4'),
                    Ul(
                        Li(A('How It Works', href='/how-it-works', cls='text-gray-500 no-underline text-sm hover:text-accent transition-colors'), cls='mb-2'),
                        Li(A('Open Investments', href='/investors', cls='text-gray-500 no-underline text-sm hover:text-accent transition-colors'), cls='mb-2'),
                        Li(A('For Artists', href='/artists', cls='text-gray-500 no-underline text-sm hover:text-accent transition-colors'), cls='mb-2'),
                        Li(A('About Us', href='/about', cls='text-gray-500 no-underline text-sm hover:text-accent transition-colors'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                Div(
                    H4('Resources', cls='text-white text-sm uppercase tracking-wider mb-4'),
                    Ul(
                        Li(A('FAQ', href='/faq', cls='text-gray-500 no-underline text-sm hover:text-accent transition-colors'), cls='mb-2'),
                        Li(A('Risk Statement', href='/risk', cls='text-gray-500 no-underline text-sm hover:text-accent transition-colors'), cls='mb-2'),
                        Li(A('Contact', href='/contact', cls='text-gray-500 no-underline text-sm hover:text-accent transition-colors'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                Div(
                    H4('Legal', cls='text-white text-sm uppercase tracking-wider mb-4'),
                    Ul(
                        Li(A('Terms of Service', href='/terms', cls='text-gray-500 no-underline text-sm hover:text-accent transition-colors'), cls='mb-2'),
                        Li(A('Privacy Policy', href='/privacy', cls='text-gray-500 no-underline text-sm hover:text-accent transition-colors'), cls='mb-2'),
                        Li(A('Risk Disclosures', href='/risk', cls='text-gray-500 no-underline text-sm hover:text-accent transition-colors'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                cls='max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12'
            ),
            Div(
                P('\u00a9 2026 Kanvas.ai. All rights reserved. Investing involves risk and can result in loss of capital.'),
                P('All investments are backed by physical artworks held in secure, climate-controlled storage.'),
                cls='max-w-7xl mx-auto mt-12 pt-8 border-t border-white/10 flex flex-col md:flex-row justify-between items-center text-sm gap-4'
            ),
        ),
        cls='bg-dark-deeper text-gray-400 pt-16 pb-8 px-8'
    )


def Page(content, active='home', title='Kanvas.ai'):
    return (
        Title(f'{title} - Fine Art Investment Platform'),
        NavBar(active),
        Main(content),
        PageFooter()
    )
