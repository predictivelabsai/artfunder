from fasthtml.common import *


LEGAL_UPDATED = "15 August 2026"


def _legal_page(title: str, intro: str, *sections):
    return Section(
        Div(
            P("Kanvas.ai", cls="text-xs uppercase tracking-[0.2em] text-gray-400 mb-4"),
            H1(title, cls="font-display text-4xl md:text-5xl font-semibold text-black mb-4"),
            P(intro, cls="text-lg text-gray-600 leading-relaxed max-w-3xl mb-3"),
            P(f"Last updated: {LEGAL_UPDATED}", cls="text-sm text-gray-400 mb-12"),
            *sections,
            cls="max-w-4xl mx-auto",
        ),
        cls="py-16 md:py-24 px-6 bg-white",
    )


def _section(title: str, *content):
    return Div(
        H2(title, cls="font-display text-2xl font-semibold text-black mb-4"),
        *content,
        cls="mb-10 text-gray-600 leading-relaxed",
    )


def _paragraph(text: str):
    return P(text, cls="mb-4")


def _items(*items):
    return Ul(*(Li(item, cls="mb-2") for item in items), cls="list-disc pl-6 mb-4")


def privacy_page():
    return _legal_page(
        "Privacy Policy",
        "This policy explains how Predictive Labs Ltd handles personal data when you use the Kanvas website, Android app, and AI art-advisory services.",
        _section(
            "Who is responsible",
            _paragraph("Predictive Labs Ltd is the data controller. We are a company registered in England and Wales under company number 14857334, with registered office at 155 Minories Street, Suite 275, London EC3N 1AD, United Kingdom."),
            P("Privacy enquiries: ", A("info@predictivelabs.ai", href="mailto:info@predictivelabs.ai", cls="underline text-black"), cls="mb-4"),
        ),
        _section(
            "Data we handle",
            _items(
                "Account data: email address, name, a securely hashed password, and Google account identity information when you choose Google Sign-In.",
                "Optional profile data: phone number, country, city, language, currency, notification settings, and art preferences.",
                "Kanvas content: prompts, AI responses, chat history, session titles, tool results, charts, and any chat link you explicitly choose to share.",
                "Safety and support content: AI-response reports, contact messages, and related correspondence.",
                "Technical data needed to operate and secure the service, such as IP address, request time, device or browser information, and server diagnostics.",
            ),
            _paragraph("The Android app requests internet access. It does not request camera, microphone, contacts, precise location, photo-library, or advertising-ID permissions."),
        ),
        _section(
            "Why we use it",
            _items(
                "Provide accounts, authentication, saved chat history, profiles, language settings, and support.",
                "Answer art-market questions, route requests to specialist AI tools, and improve the safety and reliability of responses.",
                "Protect Kanvas, prevent abuse, diagnose faults, and comply with applicable law.",
                "Send service emails and optional market updates you have selected. You can change notification preferences in your profile.",
            ),
            _paragraph("Kanvas provides research and informational art-market guidance. It does not execute purchases, hold client money or assets, or provide regulated investment services through the Android app."),
        ),
        _section(
            "Service providers and international processing",
            _paragraph("We use carefully selected providers to operate Kanvas. These may include Google for sign-in, xAI for language-model processing, Exa for web research, Postmark for transactional email, and infrastructure providers for hosting and storage. A prompt and limited recent conversation context may be sent to AI and research providers when needed to answer your request."),
            _paragraph("Some providers may process data outside the United Kingdom or European Economic Area. Where required, we use appropriate contractual and legal safeguards. We do not sell personal data and the Android app contains no third-party advertising SDK."),
        ),
        _section(
            "Sharing and public links",
            _paragraph("Chats are private unless you choose the Share function. A shared chat receives an unguessable public link. Anyone with that link can read the shared content, so do not share personal or confidential information. Delete the underlying chat or your account to disable associated shared links."),
        ),
        _section(
            "Retention and deletion",
            _paragraph("We keep account and saved-chat data while your account is active and for only as long as needed for the purposes above. Operational security logs are retained for a limited period. Data may remain in restricted backups until normal backup rotation completes and is not used for ordinary business purposes."),
            P("You can permanently delete your Kanvas account and associated profile, chats, messages, and shared links from Profile & Preferences in the Android app. You can also request deletion through our ", A("account deletion page", href="/account-deletion", cls="underline text-black"), ". We may retain limited records only when required for security, fraud prevention, dispute resolution, or law, and will explain any such retention when it applies.", cls="mb-4"),
        ),
        _section(
            "Your rights",
            _paragraph("Depending on your location, you may have rights to access, correct, erase, restrict, or receive your personal data, and to object to or withdraw consent for certain processing. Contact us to exercise these rights. You may also complain to the UK Information Commissioner's Office or your local data-protection authority."),
        ),
        _section(
            "Children and AI",
            _paragraph("Kanvas is intended for adults and is not directed to children under 18. AI responses may be incomplete or incorrect. Use the report control beside an AI response to flag unsafe, offensive, misleading, or otherwise problematic content."),
        ),
        _section(
            "Changes",
            _paragraph("We may update this policy when Kanvas or legal requirements change. We will publish the revised date here and provide additional notice where appropriate."),
        ),
    )


def account_deletion_page():
    return _legal_page(
        "Delete your Kanvas account",
        "Kanvas users can permanently delete their account and associated data either inside the Android app or by contacting us from the account email address.",
        _section(
            "Delete in the Android app",
            _items(
                "Open Kanvas and sign in.",
                "Open Profile & Preferences.",
                "Scroll to Account deletion and select Delete account.",
                "Review the warning, enter DELETE, and confirm.",
            ),
            _paragraph("The in-app flow permanently removes your Kanvas account, profile and art preferences, saved chat sessions and messages, AI-content reports associated with your account, and shared-chat links."),
        ),
        _section(
            "Request deletion without the app",
            P("Email ", A("info@predictivelabs.ai", href="mailto:info@predictivelabs.ai?subject=Kanvas%20account%20deletion%20request", cls="underline text-black"), " from the email address used for your Kanvas account. Use the subject “Kanvas account deletion request”. We may ask you to verify control of the account before deletion.", cls="mb-4"),
            A("Start an account deletion request", href="mailto:info@predictivelabs.ai?subject=Kanvas%20account%20deletion%20request", cls="inline-flex px-5 py-3 rounded-lg bg-black text-white no-underline font-medium"),
        ),
        _section(
            "What may be retained",
            _paragraph("Limited information may be retained only where required for security, fraud prevention, dispute resolution, or legal compliance. Restricted backup copies expire through normal backup rotation. We will explain any retention that applies to your request."),
            P("Read the full ", A("Kanvas Privacy Policy", href="/privacy", cls="underline text-black"), ".", cls="mb-4"),
        ),
    )
