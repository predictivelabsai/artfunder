import os
from fasthtml.common import *
from starlette.responses import RedirectResponse
import hashlib

# Components & pages
from components.layout import app_styles, Page
from pages.home import home_page
from pages.how_it_works import how_it_works_page
from pages.investors import investors_page
from pages.artists import artists_page
from pages.about import about_page
from pages.contact import contact_page

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

# Register routers
admin_router.to_app(app)
api_router.to_app(app)


# --- Auth helpers ---

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def check_auth(sess):
    return sess.get('auth')


# --- Public pages ---

@rt
def index():
    return Page(home_page(), active='home')

@rt('/how-it-works')
def how_it_works():
    return Page(how_it_works_page(), active='how-it-works', title='How It Works')

@rt
def investors():
    return Page(investors_page(), active='investors', title='Investors')

@rt
def artists():
    return Page(artists_page(), active='artists', title='Artists')

@rt
def about():
    return Page(about_page(), active='about', title='About')

@rt
def contact():
    return Page(contact_page(), active='contact', title='Contact')


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
                               cls='w-full mt-2 px-6 py-2.5 rounded-md font-semibold text-sm bg-primary text-white hover:bg-primary-light transition-colors cursor-pointer border-none'),
                        method='post', action='/login',
                        cls='bg-white p-8 rounded-lg shadow-sm max-w-md mx-auto'
                    ),
                    Div(
                        P("Don't have an account? ", A('Register', href='/register', cls='text-accent no-underline'),
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
    return login_form()

@rt('/login', methods=['POST'])
async def login_post(req, sess):
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
                            Option('Investor', value='investor'),
                            Option('Artist / Gallery', value='artist'),
                            name='role', cls=INPUT_CLS
                        ),
                    ),
                    Button('Create Account', type='submit',
                           cls='w-full mt-2 px-6 py-2.5 rounded-md font-semibold text-sm bg-primary text-white hover:bg-primary-light transition-colors cursor-pointer border-none'),
                    method='post', action='/register',
                    cls='bg-white p-8 rounded-lg shadow-sm max-w-md mx-auto'
                ),
                P('Already have an account? ', A('Login', href='/login', cls='text-accent no-underline'),
                  cls='text-center mt-6 text-gray-500 text-sm'),
                cls='max-w-7xl mx-auto'
            ),
            cls='py-20 px-8 min-h-[60vh] flex items-center'
        ),
        active='', title='Register'
    )


@rt('/register', methods=['POST'])
async def register_post(req, sess):
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
                    P(A('Login instead', href='/login', cls='text-accent no-underline'), cls='text-center'),
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
def faq():
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
                    H1('Frequently Asked Questions', cls='font-display text-4xl font-extrabold text-white mb-4'),
                    P('Find answers to common questions about Kanvas.ai.', cls='text-lg text-white/90'),
                    cls='max-w-7xl mx-auto relative z-10'
                ),
                cls='art-gradient py-16 px-8'
            ),
            Section(
                Div(*faq_items, cls='max-w-3xl mx-auto space-y-6'),
                cls='py-20 px-8 bg-gallery-cream'
            ),
        ),
        active='', title='FAQ'
    )


# --- Initialize DB on startup ---

@app.on_event("startup")
async def startup():
    try:
        init_db()
        # Create default admin if not exists
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


serve(port=int(os.environ.get('PORT', 5001)))
