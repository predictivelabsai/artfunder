from fasthtml.common import *
from utils.i18n import t, LANGUAGES, get_lang, DEFAULT_LANG


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


def _lang_switcher(lang: str = "en"):
    """Flag dropdown for language switching (pehero pattern)."""
    current = LANGUAGES.get(lang, LANGUAGES["en"])
    options = []
    for code, info in LANGUAGES.items():
        active_cls = ' font-semibold text-black' if code == lang else ''
        options.append(
            A(Span(info["flag"], cls='mr-2'), Span(info["native"], cls='text-xs'),
              href=f'/set-lang/{code}',
              cls=f'flex items-center gap-1 px-3 py-1.5 text-sm text-gray-500 hover:bg-gray-50 hover:text-black transition-colors no-underline{active_cls}')
        )
    return Div(
        Button(current["flag"],
               cls='text-base leading-none px-1.5 py-1 border border-transparent rounded hover:border-gray-200 transition-colors cursor-pointer bg-transparent',
               onclick="this.nextElementSibling.classList.toggle('hidden')"),
        Div(*options,
            cls='hidden absolute right-0 top-full mt-1 bg-white border border-gray-100 rounded-lg shadow-lg z-50 py-1 min-w-[130px] flex flex-col'),
        cls='relative',
    )


def NavBar(active='home', sess=None):
    from utils.config import settings
    login_enabled = settings().login_enabled
    lang = get_lang(sess or {})

    logged_in = sess and sess.get('auth') if login_enabled else False
    user_name = (sess.get('name', '') if sess else '') or ''

    nav_items_left = [
        ('home', '/', t('nav_home', lang)),
        ('advisory', '/app', t('nav_advisory', lang)),
        ('investors', '/investors', t('nav_collection', lang)),
        ('artists', '/artists', t('nav_artists', lang)),
        ('about', '/about', t('nav_about', lang)),
    ]
    nav_items_right = [
        ('art-index', '/app/market-map', t('nav_art_index', lang)),
        ('contact', '/contact', t('nav_contact', lang)),
    ]

    def nav_link(key, href, label):
        base = 'text-sm font-medium no-underline transition-colors duration-200'
        if key == active:
            return A(label, href=href, cls=f'{base} text-black')
        return A(label, href=href, cls=f'{base} text-gray-400 hover:text-black')

    if not login_enabled:
        auth_items = [
            Li(A(t('nav_open_app', lang), href='/app',
                 cls='bg-black text-white px-5 py-2 rounded-full font-semibold text-sm no-underline hover:bg-gray-800 transition-colors')),
        ]
    elif logged_in:
        auth_items = [
            Li(Span(user_name, cls='text-gray-400 text-sm')) if user_name else '',
            Li(A(t('nav_logout', lang), href='/logout',
                 cls='bg-black text-white px-5 py-2 rounded-full font-semibold text-sm no-underline hover:bg-gray-800 transition-colors')),
        ]
    else:
        auth_items = [
            Li(A(t('nav_login', lang), href='/login',
                 cls='bg-black text-white px-5 py-2 rounded-full font-semibold text-sm no-underline hover:bg-gray-800 transition-colors')),
        ]

    return Nav(
        Div(
            A('Kanvas', Span('.ai', cls='text-gray-400'), href='/',
              cls='font-display text-2xl font-bold text-black no-underline tracking-wide shrink-0'),
            Div(
                _lang_switcher(lang),
                Button('☰',
                       cls='md:hidden bg-transparent border-none text-black text-2xl cursor-pointer',
                       onclick="document.getElementById('nav-links').classList.toggle('hidden')"),
                cls='flex items-center gap-2 md:hidden',
            ),
            Ul(
                *[Li(nav_link(key, href, label)) for key, href, label in nav_items_left],
                Li(cls='flex-grow'),
                *[Li(nav_link(key, href, label)) for key, href, label in nav_items_right],
                Li(_lang_switcher(lang), cls='hidden md:block'),
                *auth_items,
                id='nav-links',
                cls='hidden md:flex items-center gap-8 list-none m-0 p-0 flex-grow'
            ),
            cls='max-w-7xl mx-auto flex items-center justify-between h-[70px] gap-8'
        ),
        Script("""document.addEventListener('click', function(e) {
            var dd = e.target.closest('.relative');
            document.querySelectorAll('.relative > div').forEach(function(d) {
                if (d.parentElement !== dd && !d.classList.contains('md:flex'))
                    d.classList.add('hidden');
            });
        });"""),
        cls='bg-white px-8 sticky top-0 z-50 border-b border-gray-100',
    )


def PageFooter(lang: str = "en"):
    from fasthtml.components import Footer as FooterTag
    return FooterTag(
        Div(
            Div(
                Div(
                    H3('Kanvas', Span('.ai', cls='text-gray-500'),
                       cls='font-display text-black text-xl mb-4 tracking-wide'),
                    P(t('footer_desc', lang),
                      cls='text-sm leading-relaxed text-gray-500'),
                ),
                Div(
                    H4(t('footer_platform', lang), cls='text-black text-sm uppercase tracking-wider mb-4'),
                    Ul(
                        Li(A(t('nav_advisory', lang), href='/app', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A(t('nav_collection', lang), href='/investors', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A(t('footer_for_artists', lang), href='/artists', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A('Analytics', href='/app/analytics', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                Div(
                    H4(t('footer_resources', lang), cls='text-black text-sm uppercase tracking-wider mb-4'),
                    Ul(
                        Li(A(t('nav_art_index', lang), href='/app/market-map', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A(t('nav_about', lang), href='/about', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A(t('nav_contact', lang), href='/contact', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A('Tezos Foundation', href='https://tezos.foundation/', target='_blank', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                Div(
                    H4(t('footer_legal', lang), cls='text-black text-sm uppercase tracking-wider mb-4'),
                    Ul(
                        Li(A(t('footer_terms', lang), href='/terms', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A(t('footer_privacy', lang), href='/privacy', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A(t('footer_risk', lang), href='/risk', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        cls='list-none'
                    )
                ),
                cls='max-w-7xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-12'
            ),
            Div(
                P(t('footer_copyright', lang)),
                P(t('footer_disclaimer', lang)),
                cls='max-w-7xl mx-auto mt-12 pt-8 border-t border-gray-200 flex flex-col md:flex-row justify-between items-center text-sm gap-4'
            ),
        ),
        cls='bg-white text-gray-400 pt-16 pb-8 px-8 border-t border-gray-100'
    )


def Page(content, active='home', title='Kanvas.ai', sess=None):
    lang = get_lang(sess or {})
    return (
        Title(f'{title} - AI Art Advisory & Investment'),
        NavBar(active, sess=sess),
        Main(content),
        PageFooter(lang=lang)
    )
