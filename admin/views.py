from fasthtml.common import *
from sqlalchemy import inspect, text
from db import SessionLocal, SCHEMA
from models import (
    User, Gallery, Artwork, InvestmentOpportunity, Investment,
    ProjectUpdate, Notification, FAQ, Repayment, Dividend,
    InvestorVoting, Payment, SecondaryMarket, AutoInvest
)

ar = APIRouter()

# Model registry for admin CRUD
ADMIN_MODELS = {
    'users': {'model': User, 'label': 'Users', 'list_fields': ['id', 'email', 'first_name', 'last_name', 'role', 'is_active']},
    'galleries': {'model': Gallery, 'label': 'Galleries', 'list_fields': ['id', 'name', 'registration_number']},
    'artworks': {'model': Artwork, 'label': 'Artworks', 'list_fields': ['id', 'title', 'category', 'status', 'artist_name', 'origin_country']},
    'opportunities': {'model': InvestmentOpportunity, 'label': 'Investment Opportunities', 'list_fields': ['id', 'name', 'funding_goal', 'amount_raised', 'interest_rate', 'funding_status']},
    'investments': {'model': Investment, 'label': 'Investments', 'list_fields': ['id', 'opportunity_id', 'investor_id', 'amount', 'status']},
    'updates': {'model': ProjectUpdate, 'label': 'Project Updates', 'list_fields': ['id', 'artwork_id', 'title', 'update_type', 'created_at']},
    'notifications': {'model': Notification, 'label': 'Notifications', 'list_fields': ['id', 'user_id', 'title', 'is_read']},
    'faqs': {'model': FAQ, 'label': 'FAQs', 'list_fields': ['id', 'question', 'display_order', 'is_active']},
    'repayments': {'model': Repayment, 'label': 'Repayments', 'list_fields': ['id', 'opportunity_id', 'amount', 'repayment_date', 'is_principal']},
    'dividends': {'model': Dividend, 'label': 'Dividends', 'list_fields': ['id', 'investor_id', 'opportunity_id', 'amount', 'is_paid']},
    'votings': {'model': InvestorVoting, 'label': 'Investor Votings', 'list_fields': ['id', 'opportunity_id', 'question', 'is_active']},
    'payments': {'model': Payment, 'label': 'Payments', 'list_fields': ['id', 'investor_id', 'amount', 'payment_status', 'transaction_id']},
    'secondary': {'model': SecondaryMarket, 'label': 'Secondary Market', 'list_fields': ['id', 'investment_id', 'seller_id', 'listing_price', 'status']},
    'autoinvest': {'model': AutoInvest, 'label': 'Auto Invest', 'list_fields': ['id', 'investor_id', 'max_investment_amount', 'is_active']},
}


def admin_sidebar(active=''):
    links = [A('\u2302 Dashboard', href='/admin',
               cls=f'block px-6 py-3 text-sm no-underline transition-colors {"bg-white/10 text-accent" if active == "dashboard" else "text-gray-400 hover:bg-white/10 hover:text-accent"}')]
    for key, cfg in ADMIN_MODELS.items():
        links.append(A(cfg['label'], href=f'/admin/{key}',
                       cls=f'block px-6 py-3 text-sm no-underline transition-colors {"bg-white/10 text-accent" if active == key else "text-gray-400 hover:bg-white/10 hover:text-accent"}'))
    return Div(*links, cls='w-[250px] bg-dark text-white min-h-[calc(100vh-70px)] pt-6 fixed top-[70px] left-0')


def admin_layout(content, active='dashboard'):
    return (
        Title('Kanvas.ai Admin'),
        Nav(
            Div(
                A('Kanvas', Span('.ai', cls='text-accent'), ' Admin', href='/admin',
                  cls='font-display text-xl font-bold text-white no-underline tracking-wide'),
                Div(
                    A('View Site', href='/', cls='text-gray-400 no-underline text-sm mr-6'),
                    A('Logout', href='/logout', cls='text-accent no-underline text-sm'),
                ),
                cls='max-w-7xl mx-auto flex items-center justify-between h-[70px]'
            ),
            cls='bg-dark px-8 sticky top-0 z-50 shadow-md border-b border-white/5'
        ),
        admin_sidebar(active),
        Div(content, cls='ml-[250px] p-8 min-h-[calc(100vh-70px)]')
    )


BADGE_CLASSES = {
    'green': 'inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800',
    'yellow': 'inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800',
    'red': 'inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800',
    'blue': 'inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-blue-100 text-blue-800',
    'gray': 'inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-800',
}


def status_badge(value):
    v = str(value).lower() if value else ''
    if v in ('active', 'open', 'confirmed', 'completed', 'true', 'yes'):
        color = 'green'
    elif v in ('pending', 'listed', 'draft'):
        color = 'yellow'
    elif v in ('defaulted', 'failed', 'cancelled', 'false', 'no'):
        color = 'red'
    elif v in ('funded', 'repaying'):
        color = 'blue'
    else:
        color = 'gray'
    return Span(str(value), cls=BADGE_CLASSES[color])


@ar('/admin')
def admin_dashboard():
    db = SessionLocal()
    try:
        stats = []
        for key, cfg in ADMIN_MODELS.items():
            count = db.query(cfg['model']).count()
            stats.append(
                Div(
                    H3(str(count), cls='text-3xl font-extrabold text-primary'),
                    P(cfg['label'], cls='text-sm text-gray-500 mt-1'),
                    A('View \u2192', href=f'/admin/{key}',
                      cls='block mt-2 text-accent-dark no-underline text-sm font-semibold'),
                    cls='bg-white p-6 rounded-lg shadow-sm'
                )
            )
        content = Div(
            H1('Dashboard', cls='text-3xl font-bold mb-8'),
            Div(*stats, cls='grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6'),
        )
    finally:
        db.close()
    return admin_layout(content, 'dashboard')


@ar('/admin/{model_key}')
def admin_list(model_key: str):
    if model_key not in ADMIN_MODELS:
        return admin_layout(P('Model not found.'), 'dashboard')

    cfg = ADMIN_MODELS[model_key]
    model = cfg['model']
    db = SessionLocal()
    try:
        items = db.query(model).order_by(model.id.desc()).limit(100).all()
        headers = [Th(f.replace('_', ' ').title(),
                      cls='bg-gray-50 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 border-b-2 border-gray-200')
                   for f in cfg['list_fields']]
        headers.append(Th('Actions',
                          cls='bg-gray-50 px-4 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500 border-b-2 border-gray-200'))

        rows = []
        for item in items:
            cells = []
            for f in cfg['list_fields']:
                val = getattr(item, f, '')
                td_cls = 'px-4 py-3 border-b border-gray-100 text-sm'
                if isinstance(val, bool) or (hasattr(val, 'value') and str(val.value) in ('true', 'false')):
                    cells.append(Td(status_badge(val), cls=td_cls))
                elif f in ('status', 'funding_status', 'payment_status', 'role', 'category', 'risk_level', 'update_type'):
                    cells.append(Td(status_badge(val.value if hasattr(val, 'value') else val), cls=td_cls))
                else:
                    display = str(val)[:50] if val is not None else '-'
                    cells.append(Td(display, cls=td_cls))
            cells.append(Td(
                A('Edit', href=f'/admin/{model_key}/{item.id}/edit',
                  cls='text-primary no-underline font-semibold mr-4'),
                A('Delete', href=f'/admin/{model_key}/{item.id}/delete',
                  cls='text-red-600 no-underline font-semibold',
                  onclick="return confirm('Are you sure?')"),
                cls='px-4 py-3 border-b border-gray-100 text-sm'
            ))
            rows.append(Tr(*cells, cls='hover:bg-blue-50/50'))

        content = Div(
            Div(
                H1(cfg['label'], cls='text-3xl font-bold'),
                A(f'+ Add {cfg["label"]}', href=f'/admin/{model_key}/add',
                  cls='inline-block px-5 py-2 rounded-md font-semibold text-sm no-underline bg-primary text-white hover:bg-primary-light transition-colors'),
                cls='flex justify-between items-center mb-6'
            ),
            P(f'{len(items)} records', cls='text-gray-500 mb-4 text-sm'),
            Table(Thead(Tr(*headers)), Tbody(*rows),
                  cls='w-full border-collapse bg-white rounded-lg overflow-hidden shadow-sm') if rows else P('No records found.'),
        )
    finally:
        db.close()
    return admin_layout(content, model_key)


def get_model_fields(model):
    """Get editable fields for a model."""
    mapper = inspect(model)
    fields = []
    for col in mapper.columns:
        if col.name in ('id', 'created_at', 'updated_at'):
            continue
        field_type = 'text'
        col_type = str(col.type).upper()
        if 'INT' in col_type:
            field_type = 'number'
        elif 'NUMERIC' in col_type or 'DECIMAL' in col_type:
            field_type = 'number'
        elif 'BOOL' in col_type:
            field_type = 'checkbox'
        elif 'TEXT' in col_type:
            field_type = 'textarea'
        elif 'DATE' in col_type and 'TIME' not in col_type:
            field_type = 'date'
        elif 'DATETIME' in col_type or 'TIMESTAMP' in col_type:
            field_type = 'datetime-local'
        elif 'ENUM' in col_type or hasattr(col.type, 'enums'):
            field_type = 'select'

        fields.append({
            'name': col.name,
            'type': field_type,
            'nullable': col.nullable,
            'col': col,
        })
    return fields


def render_form_field(field, value=None):
    name = field['name']
    label_text = name.replace('_', ' ').title()
    input_cls = 'w-full px-3 py-2 border border-gray-200 rounded-md text-sm mb-4 font-sans'

    if field['type'] == 'checkbox':
        checked = bool(value) if value is not None else False
        return Div(
            Label(
                Input(type='checkbox', name=name, checked=checked, value='true',
                      cls='w-auto mr-2'),
                label_text,
                cls='flex items-center text-sm font-semibold text-gray-900'
            ),
            cls='mb-4'
        )
    elif field['type'] == 'select' and hasattr(field['col'].type, 'enums'):
        enums = field['col'].type.enums
        options = [Option(e, value=e, selected=(str(value) == e if value else False)) for e in enums]
        options.insert(0, Option('-- Select --', value=''))
        return Div(Label(label_text, cls='block mb-1 font-semibold text-sm text-gray-900'),
                   Select(*options, name=name, cls=input_cls))
    elif field['type'] == 'textarea':
        return Div(Label(label_text, cls='block mb-1 font-semibold text-sm text-gray-900'),
                   Textarea(str(value or ''), name=name, cls=f'{input_cls} min-h-[100px] resize-y'))
    else:
        return Div(
            Label(label_text, cls='block mb-1 font-semibold text-sm text-gray-900'),
            Input(type=field['type'], name=name, value=str(value or ''),
                  step='0.01' if field['type'] == 'number' else None,
                  cls=input_cls)
        )


@ar('/admin/{model_key}/add', methods=['GET'])
def admin_add_form(model_key: str):
    if model_key not in ADMIN_MODELS:
        return admin_layout(P('Model not found.'), 'dashboard')

    cfg = ADMIN_MODELS[model_key]
    fields = get_model_fields(cfg['model'])
    form_fields = [render_form_field(f) for f in fields]

    content = Div(
        H1(f'Add {cfg["label"]}', cls='text-3xl font-bold mb-6'),
        Form(
            *form_fields,
            Div(
                Button('Save', type='submit',
                       cls='inline-block px-6 py-2.5 rounded-md font-semibold text-sm bg-primary text-white hover:bg-primary-light transition-colors cursor-pointer border-none mr-4'),
                A('Cancel', href=f'/admin/{model_key}',
                  cls='inline-block px-6 py-2.5 rounded-md font-semibold text-sm no-underline bg-gray-200 text-gray-900'),
            ),
            method='post', action=f'/admin/{model_key}/add',
            cls='bg-white p-8 rounded-lg shadow-sm max-w-3xl'
        )
    )
    return admin_layout(content, model_key)


@ar('/admin/{model_key}/add', methods=['POST'])
async def admin_add_save(model_key: str, req):
    if model_key not in ADMIN_MODELS:
        return RedirectResponse('/admin', status_code=303)

    cfg = ADMIN_MODELS[model_key]
    model = cfg['model']
    form = await req.form()
    fields = get_model_fields(model)

    obj = model()
    for field in fields:
        name = field['name']
        val = form.get(name, '')
        if field['type'] == 'checkbox':
            setattr(obj, name, name in form)
        elif field['type'] == 'number' and val:
            try:
                setattr(obj, name, float(val) if '.' in str(val) else int(val))
            except (ValueError, TypeError):
                pass
        elif val:
            setattr(obj, name, val)
        elif field['nullable']:
            setattr(obj, name, None)

    db = SessionLocal()
    try:
        db.add(obj)
        db.commit()
    finally:
        db.close()

    return RedirectResponse(f'/admin/{model_key}', status_code=303)


@ar('/admin/{model_key}/{item_id}/edit', methods=['GET'])
def admin_edit_form(model_key: str, item_id: int):
    if model_key not in ADMIN_MODELS:
        return admin_layout(P('Model not found.'), 'dashboard')

    cfg = ADMIN_MODELS[model_key]
    model = cfg['model']
    db = SessionLocal()
    try:
        obj = db.query(model).get(item_id)
        if not obj:
            return admin_layout(P('Record not found.'), model_key)

        fields = get_model_fields(model)
        form_fields = [render_form_field(f, getattr(obj, f['name'], None)) for f in fields]
    finally:
        db.close()

    content = Div(
        H1(f'Edit {cfg["label"]} #{item_id}', cls='text-3xl font-bold mb-6'),
        Form(
            *form_fields,
            Div(
                Button('Save Changes', type='submit',
                       cls='inline-block px-6 py-2.5 rounded-md font-semibold text-sm bg-primary text-white hover:bg-primary-light transition-colors cursor-pointer border-none mr-4'),
                A('Cancel', href=f'/admin/{model_key}',
                  cls='inline-block px-6 py-2.5 rounded-md font-semibold text-sm no-underline bg-gray-200 text-gray-900'),
            ),
            method='post', action=f'/admin/{model_key}/{item_id}/edit',
            cls='bg-white p-8 rounded-lg shadow-sm max-w-3xl'
        )
    )
    return admin_layout(content, model_key)


@ar('/admin/{model_key}/{item_id}/edit', methods=['POST'])
async def admin_edit_save(model_key: str, item_id: int, req):
    if model_key not in ADMIN_MODELS:
        return RedirectResponse('/admin', status_code=303)

    cfg = ADMIN_MODELS[model_key]
    model = cfg['model']
    form = await req.form()
    fields = get_model_fields(model)

    db = SessionLocal()
    try:
        obj = db.query(model).get(item_id)
        if not obj:
            return RedirectResponse(f'/admin/{model_key}', status_code=303)

        for field in fields:
            name = field['name']
            val = form.get(name, '')
            if field['type'] == 'checkbox':
                setattr(obj, name, name in form)
            elif field['type'] == 'number' and val:
                try:
                    setattr(obj, name, float(val) if '.' in str(val) else int(val))
                except (ValueError, TypeError):
                    pass
            elif val:
                setattr(obj, name, val)
            elif field['nullable']:
                setattr(obj, name, None)

        db.commit()
    finally:
        db.close()

    return RedirectResponse(f'/admin/{model_key}', status_code=303)


@ar('/admin/{model_key}/{item_id}/delete')
def admin_delete(model_key: str, item_id: int):
    if model_key not in ADMIN_MODELS:
        return RedirectResponse('/admin', status_code=303)

    cfg = ADMIN_MODELS[model_key]
    model = cfg['model']
    db = SessionLocal()
    try:
        obj = db.query(model).get(item_id)
        if obj:
            db.delete(obj)
            db.commit()
    finally:
        db.close()

    return RedirectResponse(f'/admin/{model_key}', status_code=303)
