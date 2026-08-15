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

    nav_items = [
        ('home', '/', t('nav_home', lang)),
        ('advisory', '/app', t('nav_advisory', lang)),
        ('investors', '/investors', t('nav_collection', lang)),
        ('artists', '/artists', t('nav_artists', lang)),
        ('galleries', '/galleries', 'Galleries'),
        ('about', '/about', t('nav_about', lang)),
        ('art-index', '/app/market-map', t('nav_art_index', lang)),
        ('contact', '/contact', t('nav_contact', lang)),
    ]

    def nav_link(key, href, label):
        if key == active:
            return A(label, href=href, cls='text-sm text-black hover:text-black transition-colors no-underline')
        return A(label, href=href, cls='text-sm text-gray-400 hover:text-black transition-colors no-underline')

    nav_links = [Li(nav_link(k, h, l)) for k, h, l in nav_items]

    if login_enabled:
        if logged_in:
            cta = A(t('nav_logout', lang), href='/logout',
                    cls='inline-flex items-center px-4 py-2 rounded-full text-xs font-medium bg-black text-white hover:bg-gray-800 transition-colors no-underline')
        else:
            cta = A(t('nav_login', lang), href='/login',
                    cls='inline-flex items-center px-4 py-2 rounded-full text-xs font-medium bg-black text-white hover:bg-gray-800 transition-colors no-underline')
    else:
        cta = A(t('nav_login', lang), href='/signin',
                cls='inline-flex items-center px-4 py-2 rounded-full text-xs font-medium bg-black text-white hover:bg-gray-800 transition-colors no-underline')

    mobile_links = [
        A(l, href=h,
          cls=f'block px-4 py-3 text-sm font-sans {"text-black" if k == active else "text-gray-400"} hover:text-black transition-colors no-underline',
          data_testid=f'mobile-nav-{k}')
        for k, h, l in nav_items
    ]

    hamburger = Button(
        Span(cls='block w-5 h-0.5 bg-black mb-1 transition-all', id='bar1'),
        Span(cls='block w-5 h-0.5 bg-black mb-1 transition-all', id='bar2'),
        Span(cls='block w-5 h-0.5 bg-black transition-all', id='bar3'),
        cls='lg:hidden flex flex-col justify-center items-center p-2 bg-transparent border-none cursor-pointer',
        id='mobile-menu-btn',
        aria_label='Open menu',
        data_testid='mobile-menu-btn',
        onclick="document.getElementById('mobile-menu').classList.toggle('hidden')",
    )

    mobile_menu = Div(
        *mobile_links,
        Div(cta, cls='px-4 py-3'),
        id='mobile-menu',
        data_testid='mobile-menu',
        cls='hidden lg:hidden bg-white border-t border-gray-100',
    )

    return Nav(
        Div(
            A('Kanvas', Span('.ai', cls='text-gray-400'), href='/',
              cls='font-display text-xl font-bold text-black no-underline tracking-tight shrink-0'),
            Ul(*nav_links, cls='hidden lg:flex items-center gap-6 list-none m-0 p-0'),
            Div(
                _lang_switcher(lang),
                cta,
                hamburger,
                cls='flex items-center gap-3',
            ),
            cls='max-w-7xl mx-auto px-5 flex items-center justify-between h-16 gap-4',
        ),
        mobile_menu,
        Script("""document.addEventListener('click', function(e) {
            var dd = e.target.closest('.relative');
            document.querySelectorAll('.relative > div').forEach(function(d) {
                if (d.parentElement !== dd) d.classList.add('hidden');
            });
        });"""),
        cls='bg-white/80 backdrop-blur-md sticky top-0 z-50 border-b border-gray-100',
        style='display:block',
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
                        Li(A(t('nav_art_index', lang), href='/app/market-map', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A('Analytics', href='/app/analytics', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
                        Li(A('Galleries', href='/galleries', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
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
                        Li(A('Account deletion', href='/account-deletion', cls='text-gray-500 no-underline text-sm hover:text-black transition-colors'), cls='mb-2'),
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
