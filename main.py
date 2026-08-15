import os
from fasthtml.common import *
from starlette.responses import RedirectResponse
from starlette.staticfiles import StaticFiles
import hashlib

# Components & pages
from components.layout import app_styles, Page
from pages.home import home_page
from pages.how_it_works import how_it_works_page
from pages.investors import investors_page
from pages.artists import artists_page
from pages.about import about_page
from pages.contact import contact_page
from pages.galleries import galleries_page
from pages.legal import privacy_page, account_deletion_page

# Admin & API
from admin.views import ar as admin_router
from api.routes import ar as api_router

# Database
from db import init_db, SessionLocal
from models import User

# Initialize app with styles
app, rt = fast_app(
    hdrs=(app_styles(),),
    secret_key='kanvas-test-app-2026',
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/docs", StaticFiles(directory="docs"), name="docs")

# Register routers
admin_router.to_app(app)
api_router.to_app(app)

# Register chat routes
from chat.routes import register_chat_routes
from chat.analytics import register_analytics_routes
from chat.market_map import register_market_map_routes
register_chat_routes(rt)
register_analytics_routes(rt)
register_market_map_routes(rt)

from game.routes import register_game_routes
register_game_routes(rt)

from auth import register_auth_routes
register_auth_routes(rt)

from api.mobile_auth import register_mobile_auth_routes
register_mobile_auth_routes(rt)

# --- Mount FastAPI API at /api/v1 (optional) ---
try:
    from api.fastapi_app import api_app
    app.mount("/api/v1", api_app)
    print("INFO:     FastAPI API mounted at /api/v1 (docs: /api/v1/docs)")
except ImportError as e:
    print(f"WARNING:  FastAPI not available, /api/v1 not mounted: {e}")
except Exception as e:
    print(f"ERROR:    Failed to mount FastAPI API: {e}")


# --- Auth helpers ---

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def check_auth(sess):
    return sess.get('auth')


# --- Language switching ---

@rt('/set-lang/{code}')
def set_language(code: str, sess):
    from utils.i18n import set_lang, LANGUAGES
    if code in LANGUAGES:
        set_lang(sess, code)
    return RedirectResponse('/', status_code=303)


# --- Public pages ---

@rt
def index(sess):
    return Page(home_page(sess=sess), active='home', sess=sess)

@rt('/how-it-works')
def how_it_works(sess):
    return Page(how_it_works_page(), active='how-it-works', title='How It Works', sess=sess)

@rt
def investors(sess):
    return Page(investors_page(), active='investors', title='Collection', sess=sess)

@rt
def artists(sess):
    return Page(artists_page(), active='artists', title='Artists', sess=sess)

@rt
def about(sess):
    return Page(about_page(), active='about', title='About', sess=sess)

@rt
def contact(sess):
    return Page(contact_page(), active='contact', title='Contact', sess=sess)

@rt
def galleries(sess):
    return Page(galleries_page(sess=sess), active='galleries', title='Galleries & Auctions', sess=sess)

@rt('/privacy')
def privacy(sess):
    return Page(privacy_page(), title='Privacy Policy', sess=sess)

@rt('/account-deletion')
def account_deletion(sess):
    return Page(account_deletion_page(), title='Delete your account', sess=sess)


# --- Sign-in page ---

GOOGLE_SVG = '<svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg"><path d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.615z" fill="#4285F4"/><path d="M9 18c2.43 0 4.467-.806 5.956-2.18l-2.908-2.259c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 009 18z" fill="#34A853"/><path d="M3.964 10.71c-.18-.54-.282-1.117-.282-1.71s.102-1.17.282-1.71V4.958H.957A8.996 8.996 0 000 9s.348 1.452.957 2.042l3.007-2.332z" fill="#FBBC05"/><path d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 00.957 4.958L3.964 7.29C4.672 5.163 6.656 3.58 9 3.58z" fill="#EA4335"/></svg>'

@rt('/signin')
def signin_page(sess):
    from utils.session import get_user_email
    if get_user_email(sess):
        return RedirectResponse('/app', status_code=303)

    INPUT = 'w-full px-3 py-2.5 border border-gray-200 rounded-lg text-sm font-sans focus:outline-none focus:border-black transition-colors'
    BTN = 'w-full py-2.5 rounded-lg font-semibold text-sm cursor-pointer border-none transition-colors'

    return Page(
        Div(
        Style("""
        .auth-tab { flex:1; padding:8px 0; background:none; border:none; border-bottom:2px solid transparent;
                    font-size:14px; font-weight:500; color:#6B7280; cursor:pointer; transition:color .15s,border-color .15s; }
        .auth-tab:hover { color:#1A1A1A; }
        .auth-tab.active { color:#1A1A1A; border-bottom-color:#1A1A1A; }
        .google-btn { display:flex; align-items:center; justify-content:center; gap:10px; width:100%; padding:10px 0;
                      border:1px solid #E5E5E5; border-radius:8px; background:#fff; text-decoration:none;
                      font-size:14px; font-weight:500; color:#1A1A1A; cursor:pointer; transition:background .15s; }
        .google-btn:hover { background:#F9FAFB; border-color:#ccc; }
        .google-btn-icon { display:flex; align-items:center; }
        .google-btn-text { font-family:'Inter',sans-serif; }
        .google-divider { display:flex; align-items:center; gap:12px; margin:16px 0; }
        .google-divider-line { flex:1; height:1px; background:#E5E5E5; }
        .google-divider-text { font-size:12px; color:#9CA3AF; }
        """),
        Section(
            Div(
                Div(
                    H2('Welcome to Kanvas', Span('.ai', cls='text-gray-400'),
                       cls='font-display text-3xl text-center mb-2'),
                    P('AI-powered art advisory & market intelligence',
                      cls='text-sm text-gray-400 text-center mb-8'),

                    # Tab switcher
                    Div(
                        Button('Sign In', id='si-tab-login', cls='auth-tab active',
                               onclick="siTab('login')"),
                        Button('Register', id='si-tab-register', cls='auth-tab',
                               onclick="siTab('register')"),
                        cls='flex border-b border-gray-200 mb-6',
                    ),

                    # ── Login form ──
                    Div(
                        A(
                            Span(NotStr(GOOGLE_SVG), cls='google-btn-icon'),
                            Span('Continue with Google', cls='google-btn-text'),
                            href='/auth/google',
                            cls='google-btn',
                        ),
                        Div(Span(cls='google-divider-line'), Span('or', cls='google-divider-text'), Span(cls='google-divider-line'), cls='google-divider'),
                        Input(type='email', id='si-email', placeholder='Email', cls=INPUT,
                              onkeydown="if(event.key==='Enter')document.getElementById('si-pass').focus()"),
                        Input(type='password', id='si-pass', placeholder='Password', cls=INPUT + ' mt-3',
                              onkeydown="if(event.key==='Enter')siLogin()"),
                        Div(
                            A('Forgot password?', href='#', onclick="siTab('forgot');return false",
                              cls='text-xs text-gray-400 hover:text-black'),
                            cls='text-right mt-1 mb-4',
                        ),
                        Div(id='si-login-err', cls='text-red-500 text-xs mb-3'),
                        Button('Sign In', onclick='siLogin()', cls=BTN + ' bg-black text-white hover:bg-gray-800'),
                        id='si-form-login',
                    ),

                    # ── Register form ──
                    Div(
                        Input(type='text', id='si-reg-name', placeholder='Name (optional)', cls=INPUT),
                        Input(type='email', id='si-reg-email', placeholder='Email', cls=INPUT + ' mt-3'),
                        Input(type='password', id='si-reg-pass', placeholder='Password (min 6 characters)', cls=INPUT + ' mt-3',
                              onkeydown="if(event.key==='Enter')siRegister()"),
                        Div(id='si-reg-err', cls='text-red-500 text-xs mb-3 mt-3'),
                        Div(id='si-reg-ok', cls='text-green-600 text-xs mb-3'),
                        Button('Create Account', onclick='siRegister()', cls=BTN + ' bg-black text-white hover:bg-gray-800 mt-2'),
                        Div(Span(cls='google-divider-line'), Span('or', cls='google-divider-text'), Span(cls='google-divider-line'), cls='google-divider mt-4'),
                        A(
                            Span(NotStr(GOOGLE_SVG), cls='google-btn-icon'),
                            Span('Sign up with Google', cls='google-btn-text'),
                            href='/auth/google',
                            cls='google-btn',
                        ),
                        id='si-form-register',
                        style='display:none',
                    ),

                    # ── Forgot password form ──
                    Div(
                        P('Enter your email to receive a password reset link.',
                          cls='text-sm text-gray-500 mb-4'),
                        Input(type='email', id='si-forgot-email', placeholder='Email', cls=INPUT,
                              onkeydown="if(event.key==='Enter')siForgot()"),
                        Div(id='si-forgot-msg', cls='text-sm mb-3 mt-3'),
                        Button('Send Reset Link', onclick='siForgot()', cls=BTN + ' bg-black text-white hover:bg-gray-800 mt-2'),
                        P(A('Back to sign in', href='#', onclick="siTab('login');return false",
                            cls='text-sm text-gray-400 hover:text-black'),
                          cls='text-center mt-4'),
                        id='si-form-forgot',
                        style='display:none',
                    ),

                    cls='bg-white p-8 md:p-10 rounded-2xl shadow-sm border border-gray-100 w-full max-w-md',
                ),
                cls='flex justify-center items-center',
            ),
            cls='py-20 px-6 min-h-[70vh] flex items-center justify-center bg-gray-50/60',
        ),
        Script("""
        function siTab(t) {
            document.getElementById('si-form-login').style.display = t==='login' ? 'block' : 'none';
            document.getElementById('si-form-register').style.display = t==='register' ? 'block' : 'none';
            document.getElementById('si-form-forgot').style.display = t==='forgot' ? 'block' : 'none';
            var tl = document.getElementById('si-tab-login'), tr = document.getElementById('si-tab-register');
            tl.classList.toggle('active', t==='login');
            tr.classList.toggle('active', t==='register');
            ['si-login-err','si-reg-err','si-reg-ok','si-forgot-msg'].forEach(function(id){
                var el=document.getElementById(id); if(el) el.textContent='';
            });
        }
        async function siLogin() {
            var email = (document.getElementById('si-email')||{}).value||'';
            var pass = (document.getElementById('si-pass')||{}).value||'';
            var err = document.getElementById('si-login-err');
            if (!email.trim()||!pass) { if(err) err.textContent='Email and password are required'; return; }
            try {
                var r = await fetch('/auth/login', {method:'POST', body: new URLSearchParams({email:email.trim(),password:pass})});
                var d = await r.json();
                if (r.ok && d.ok) { window.location.href='/app'; }
                else if (d.error==='no_password') { if(err) err.textContent='Please set a password for your account'; }
                else { if(err) err.textContent=d.error||'Invalid email or password'; }
            } catch(e) { if(err) err.textContent='Network error'; }
        }
        async function siRegister() {
            var name = (document.getElementById('si-reg-name')||{}).value||'';
            var email = (document.getElementById('si-reg-email')||{}).value||'';
            var pass = (document.getElementById('si-reg-pass')||{}).value||'';
            var err = document.getElementById('si-reg-err'), ok = document.getElementById('si-reg-ok');
            if(err) err.textContent=''; if(ok) ok.textContent='';
            if (!email.trim()||!pass) { if(err) err.textContent='Email and password are required'; return; }
            if (pass.length<6) { if(err) err.textContent='Password must be at least 6 characters'; return; }
            try {
                var r = await fetch('/auth/register', {method:'POST', body: new URLSearchParams({name:name,email:email.trim(),password:pass})});
                var d = await r.json();
                if (r.ok && d.ok) { if(ok) ok.textContent=d.message||'Check your email to verify your account'; }
                else { if(err) err.textContent=d.error||'Registration failed'; }
            } catch(e) { if(err) err.textContent='Network error'; }
        }
        async function siForgot() {
            var email = (document.getElementById('si-forgot-email')||{}).value||'';
            var msg = document.getElementById('si-forgot-msg');
            if (!email.trim()) { if(msg){msg.textContent='Please enter your email';msg.className='text-red-500 text-sm mb-3 mt-3';} return; }
            try {
                var r = await fetch('/auth/forgot', {method:'POST', body: new URLSearchParams({email:email.trim()})});
                var d = await r.json();
                if(msg){msg.textContent=d.message||'If an account exists, a reset link has been sent';msg.className='text-green-600 text-sm mb-3 mt-3';}
            } catch(e) { if(msg){msg.textContent='Network error';msg.className='text-red-500 text-sm mb-3 mt-3';} }
        }
        """),
        ),
        active='', title='Sign In', sess=sess,
    )


# --- Auth pages ---

INPUT_CLS = 'w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-4 font-sans'

def login_form(error=None, email=''):
    return Page(
        Section(
            Div(
                Div(
                    Div(error, cls='bg-red-50 text-red-800 border border-red-200 px-4 py-3 rounded-lg mb-4 text-sm') if error else '',
                    H2('Login', cls='font-display text-3xl text-center mb-6'),
                    Form(
                        Div(
                            Label('Email', cls='block mb-1 font-semibold text-sm text-gray-900'),
                            Input(type='email', name='email', placeholder='you@example.com', value=email, required=True, cls=INPUT_CLS),
                        ),
                        Div(
                            Label('Password', cls='block mb-1 font-semibold text-sm text-gray-900'),
                            Input(type='password', name='password', placeholder='Your password', required=True, cls=INPUT_CLS),
                        ),
                        Button('Sign In', type='submit',
                               cls='w-full mt-2 px-6 py-2.5 rounded-full font-semibold text-sm bg-black text-white hover:bg-gray-800 transition-colors cursor-pointer border-none'),
                        method='post', action='/login',
                        cls='bg-white p-8 rounded-lg shadow-sm max-w-md mx-auto'
                    ),
                    Div(
                        P("Don't have an account? ", A('Register', href='/register', cls='text-black no-underline font-semibold'),
                          cls='text-center mt-6 text-gray-500 text-sm'),
                    ),
                ),
                cls='max-w-7xl mx-auto'
            ),
            cls='py-20 px-8 min-h-[60vh] flex items-center'
        ),
        active='', title='Login'
    )

@rt('/login', methods=['GET'])
def login_get():
    from utils.config import settings
    if not settings().login_enabled:
        return RedirectResponse('/app', status_code=303)
    return login_form()

@rt('/login', methods=['POST'])
async def login_post(req, sess):
    from utils.config import settings
    if not settings().login_enabled:
        return RedirectResponse('/app', status_code=303)
    form = await req.form()
    email = form.get('email', '')
    password = form.get('password', '')

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user and user.password_hash == hash_password(password):
            sess['auth'] = user.id
            sess['email'] = user.email
            sess['role'] = user.role.value if hasattr(user.role, 'value') else user.role
            sess['name'] = user.full_name
            if user.is_staff:
                return RedirectResponse('/admin', status_code=303)
            return RedirectResponse('/', status_code=303)
    finally:
        db.close()

    return login_form(error='Invalid email or password.', email=email)


@rt('/register', methods=['GET'])
def register():
    from utils.config import settings
    if not settings().login_enabled:
        return RedirectResponse('/app', status_code=303)
    return Page(
        Section(
            Div(
                H2('Create Account', cls='font-display text-3xl text-center mb-6'),
                Form(
                    Div(Label('First Name', cls='block mb-1 font-semibold text-sm text-gray-900'),
                        Input(type='text', name='first_name', required=True, cls=INPUT_CLS)),
                    Div(Label('Last Name', cls='block mb-1 font-semibold text-sm text-gray-900'),
                        Input(type='text', name='last_name', required=True, cls=INPUT_CLS)),
                    Div(Label('Email', cls='block mb-1 font-semibold text-sm text-gray-900'),
                        Input(type='email', name='email', required=True, cls=INPUT_CLS)),
                    Div(Label('Password', cls='block mb-1 font-semibold text-sm text-gray-900'),
                        Input(type='password', name='password', minlength='8', required=True, cls=INPUT_CLS)),
                    Div(
                        Label('I am a', cls='block mb-1 font-semibold text-sm text-gray-900'),
                        Select(
                            Option('Collector / Investor', value='investor'),
                            Option('Artist / Gallery', value='artist'),
                            name='role', cls=INPUT_CLS
                        ),
                    ),
                    Button('Create Account', type='submit',
                           cls='w-full mt-2 px-6 py-2.5 rounded-full font-semibold text-sm bg-black text-white hover:bg-gray-800 transition-colors cursor-pointer border-none'),
                    method='post', action='/register',
                    cls='bg-white p-8 rounded-lg shadow-sm max-w-md mx-auto'
                ),
                P('Already have an account? ', A('Login', href='/login', cls='text-black no-underline font-semibold'),
                  cls='text-center mt-6 text-gray-500 text-sm'),
                cls='max-w-7xl mx-auto'
            ),
            cls='py-20 px-8 min-h-[60vh] flex items-center'
        ),
        active='', title='Register'
    )


@rt('/register', methods=['POST'])
async def register_post(req, sess):
    from utils.config import settings
    if not settings().login_enabled:
        return RedirectResponse('/app', status_code=303)
    form = await req.form()
    email = form.get('email', '')
    password = form.get('password', '')
    first_name = form.get('first_name', '')
    last_name = form.get('last_name', '')
    role = form.get('role', 'investor')

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            return Page(
                Section(Div(
                    Div('An account with this email already exists.',
                        cls='bg-red-50 text-red-800 border border-red-200 px-4 py-3 rounded-lg mb-4 text-sm'),
                    H2('Create Account', cls='font-display text-3xl text-center mb-6'),
                    P(A('Login instead', href='/login', cls='text-black no-underline font-semibold'), cls='text-center'),
                    cls='max-w-7xl mx-auto'
                ), cls='py-20 px-8'),
                active='', title='Register'
            )

        user = User(
            email=email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=role,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        sess['auth'] = user.id
        sess['email'] = user.email
        sess['role'] = role
        sess['name'] = f'{first_name} {last_name}'.strip()
    finally:
        db.close()

    return RedirectResponse('/', status_code=303)


@rt
def logout(sess):
    sess.clear()
    return RedirectResponse('/', status_code=303)


# --- FAQ page ---

@rt
def faq(sess):
    from models import FAQ
    db = SessionLocal()
    try:
        faqs = db.query(FAQ).filter(FAQ.is_active == True).order_by(FAQ.display_order).all()
        faq_items = []
        for f in faqs:
            faq_items.append(Div(
                H3(f.question, cls='text-lg font-bold mb-3'),
                P(f.answer, cls='text-gray-500 text-sm leading-relaxed'),
                cls='bg-white rounded-xl p-8 shadow-sm border border-gray-100'
            ))
        if not faq_items:
            faq_items = [P('No FAQs available yet.', cls='text-gray-500 text-center')]
    finally:
        db.close()

    return Page(
        Div(
            Section(
                Div(
                    H1('Frequently Asked Questions', cls='font-display text-4xl font-extrabold text-black mb-4'),
                    P('Find answers to common questions about Kanvas.ai.', cls='text-lg text-gray-500'),
                    cls='max-w-7xl mx-auto relative z-10'
                ),
                cls='bg-white py-16 px-8'
            ),
            Section(
                Div(*faq_items, cls='max-w-3xl mx-auto space-y-6'),
                cls='py-20 px-8 bg-gray-50'
            ),
        ),
        active='', title='FAQ', sess=sess
    )


# --- Email digest scheduler ---

def _start_digest_scheduler():
    """Background thread that sends the art deals digest on a schedule.

    Defaults to WEEKLY on Saturday. The send itself is de-duplicated at the DB
    level (scripts.daily_deals._acquire_digest_lock), so it is safe for this
    scheduler to run in multiple Coolify containers — only one actually sends.

    Env: DIGEST_FREQUENCY = weekly (default) | daily | off
         DIGEST_HOUR      = 7   (0-23)
         DIGEST_WEEKDAY   = 5   (0=Mon … 6=Sun; 5 = Saturday, weekly only)
    """
    import threading
    import time as _time
    from datetime import datetime, timedelta

    freq = os.environ.get("DIGEST_FREQUENCY", "weekly").strip().lower()
    hour = int(os.environ.get("DIGEST_HOUR", "7"))
    weekday = int(os.environ.get("DIGEST_WEEKDAY", "5"))  # Saturday

    if freq == "off":
        print("INFO:     Digest scheduler disabled (DIGEST_FREQUENCY=off)", flush=True)
        return

    def _run_digest():
        try:
            from scripts.daily_deals import main as digest_main
            import sys
            sys.argv = ["daily_deals", "--all"]
            digest_main()
        except SystemExit:
            pass  # daily_deals exits non-zero on partial send failure
        except Exception as e:
            print(f"ERROR:    Digest error: {e}", flush=True)

    def _next_fire(now):
        target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        if freq == "daily":
            if target <= now:
                target += timedelta(days=1)
            return target
        # weekly
        target += timedelta(days=(weekday - target.weekday()) % 7)
        if target <= now:
            target += timedelta(weeks=1)
        return target

    def _loop():
        while True:
            now = datetime.now()
            target = _next_fire(now)
            wait = (target - now).total_seconds()
            print(f"INFO:     Digest ({freq}) scheduled for {target.strftime('%a %Y-%m-%d %H:%M')} ({wait/3600:.1f}h from now)", flush=True)
            _time.sleep(max(wait, 1))
            _run_digest()

    t = threading.Thread(target=_loop, daemon=True)
    t.start()


# --- Initialize DB on startup ---

@app.on_event("startup")
async def startup():
    try:
        init_db()
        db = SessionLocal()
        try:
            admin = db.query(User).filter(User.email == 'admin@kanvas.ai').first()
            if not admin:
                admin = User(
                    email='admin@kanvas.ai',
                    password_hash=hash_password('admin123'),
                    first_name='Admin',
                    last_name='User',
                    role='admin',
                    is_verified=True,
                    is_active=True,
                    is_staff=True,
                )
                db.add(admin)
                db.commit()
        finally:
            db.close()
    except Exception as e:
        print(f"DB init warning: {e}")

    if os.environ.get("DIGEST_ENABLED", "1") == "1":
        _start_digest_scheduler()


serve(port=int(os.environ.get('PORT', 5009)))
