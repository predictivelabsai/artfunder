"""Seed the database with sample artworks and investment opportunities."""
import os
import sys
import hashlib
from datetime import date, datetime
from decimal import Decimal

# Allow running from tasks/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault("DB_URL", os.environ.get("DB_URL", ""))

from db import init_db, SessionLocal
from models import (
    User, Artwork, InvestmentOpportunity, FAQ,
    ArtCategory, ArtworkStatus, FundingStatus, RiskLevel, UserRole
)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def seed():
    init_db()
    db = SessionLocal()

    try:
        # Check if artworks already exist
        if db.query(Artwork).count() > 0:
            print("Artworks already seeded, skipping.")
            return

        # Create admin if not exists
        admin = db.query(User).filter(User.email == 'admin@kanvas.ai').first()
        if not admin:
            admin = User(
                email='admin@kanvas.ai',
                password_hash=hash_password('admin123'),
                first_name='Admin', last_name='User',
                role='admin', is_verified=True, is_active=True, is_staff=True,
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)

        # Create sample artist user
        artist_user = db.query(User).filter(User.email == 'gallery@kanvas.ai').first()
        if not artist_user:
            artist_user = User(
                email='gallery@kanvas.ai',
                password_hash=hash_password('gallery123'),
                first_name='Chelsea', last_name='Gallery',
                role='artist', is_verified=True, is_active=True,
            )
            db.add(artist_user)
            db.commit()
            db.refresh(artist_user)

        # Create sample investor
        investor = db.query(User).filter(User.email == 'investor@kanvas.ai').first()
        if not investor:
            investor = User(
                email='investor@kanvas.ai',
                password_hash=hash_password('investor123'),
                first_name='James', last_name='Collector',
                role='investor', is_verified=True, is_active=True,
            )
            db.add(investor)
            db.commit()
            db.refresh(investor)

        # Sample artworks
        artworks_data = [
            {
                'title': 'Composition in Red, Blue and Yellow',
                'description': 'A striking abstract composition featuring bold primary colors arranged in geometric forms. This work represents the artist\'s exploration of pure abstraction and the relationship between color and form. Museum-exhibited and featured in major auction catalogs.',
                'category': 'painting',
                'status': 'active',
                'artist_name': 'Willem de Kooning',
                'medium': 'Oil on canvas',
                'origin_country': 'United States',
                'year_created': '1957',
                'dimensions': '152 x 122 cm',
                'estimated_value': Decimal('2800000'),
                'acquisition_cost': Decimal('2200000'),
                'appreciation_rate': Decimal('12.5'),
                'provenance': 'Private collection, New York; Christie\'s New York, 2018; Private collection, London',
                'image_url': '',
            },
            {
                'title': 'Untitled (Ocean Park Series)',
                'description': 'Part of the celebrated Ocean Park series, this luminous painting captures the atmospheric light of the Southern California coastline through layers of translucent color. A masterwork of postwar American abstraction.',
                'category': 'painting',
                'status': 'active',
                'artist_name': 'Richard Diebenkorn',
                'medium': 'Oil on canvas',
                'origin_country': 'United States',
                'year_created': '1971',
                'dimensions': '236 x 206 cm',
                'estimated_value': Decimal('4500000'),
                'acquisition_cost': Decimal('3600000'),
                'appreciation_rate': Decimal('14.2'),
                'provenance': 'Artist\'s estate; Gagosian Gallery; Private collection, Switzerland',
                'image_url': '',
            },
            {
                'title': 'Red Balloon over Paris',
                'description': 'A vibrant contemporary sculpture in powder-coated stainless steel. The playful form belies sophisticated engineering and craftsmanship. One of an edition of three, with siblings in major museum collections.',
                'category': 'sculpture',
                'status': 'active',
                'artist_name': 'Jeff Koons',
                'medium': 'Mirror-polished stainless steel with transparent color coating',
                'origin_country': 'United States',
                'year_created': '2012',
                'dimensions': '307 x 163 x 124 cm',
                'estimated_value': Decimal('8500000'),
                'acquisition_cost': Decimal('6800000'),
                'appreciation_rate': Decimal('15.8'),
                'provenance': 'David Zwirner Gallery, New York; Private collection, Qatar',
                'image_url': '',
            },
            {
                'title': 'Rhein II',
                'description': 'An iconic large-format photograph depicting the Rhine river in a stripped-down, almost abstract composition. This edition print is from the artist\'s most celebrated and valuable series.',
                'category': 'photography',
                'status': 'active',
                'artist_name': 'Andreas Gursky',
                'medium': 'Chromogenic color print, mounted on Plexiglas',
                'origin_country': 'Germany',
                'year_created': '1999',
                'dimensions': '185.4 x 363.5 cm',
                'estimated_value': Decimal('3200000'),
                'acquisition_cost': Decimal('2500000'),
                'appreciation_rate': Decimal('11.3'),
                'provenance': 'Matthew Marks Gallery; Private collection, Chicago; Sotheby\'s London, 2022',
                'image_url': '',
            },
            {
                'title': 'Girl with Balloon',
                'description': 'One of Banksy\'s most iconic images, this limited edition screen print on paper shows a girl reaching for a heart-shaped balloon. Authenticated by Pest Control. Pristine condition.',
                'category': 'print_art',
                'status': 'active',
                'artist_name': 'Banksy',
                'medium': 'Screen print on paper',
                'origin_country': 'United Kingdom',
                'year_created': '2004',
                'dimensions': '70 x 50 cm',
                'estimated_value': Decimal('850000'),
                'acquisition_cost': Decimal('680000'),
                'appreciation_rate': Decimal('18.5'),
                'provenance': 'Pictures on Walls; Private collection, London; Phillips London, 2023',
                'image_url': '',
            },
            {
                'title': 'Infinity Mirror Room',
                'description': 'A rare mixed media installation piece combining mirrors, LEDs, and painted elements. Creates an immersive experience of infinite reflection. Complete with artist certificate and installation specifications.',
                'category': 'mixed_media',
                'status': 'active',
                'artist_name': 'Yayoi Kusama',
                'medium': 'Wood, mirrors, LED lights, acrylic paint',
                'origin_country': 'Japan',
                'year_created': '2016',
                'dimensions': '250 x 250 x 250 cm (room installation)',
                'estimated_value': Decimal('5200000'),
                'acquisition_cost': Decimal('4100000'),
                'appreciation_rate': Decimal('16.7'),
                'provenance': 'Victoria Miro Gallery, London; Private collection, Tokyo',
                'image_url': '',
            },
            {
                'title': 'Water Lilies (Nympheas)',
                'description': 'A magnificent example from Monet\'s celebrated Water Lilies series, painted at his garden in Giverny. Rich impasto and luminous color capture the play of light on the pond surface.',
                'category': 'painting',
                'status': 'funded',
                'artist_name': 'Claude Monet',
                'medium': 'Oil on canvas',
                'origin_country': 'France',
                'year_created': '1906',
                'dimensions': '89 x 100 cm',
                'estimated_value': Decimal('35000000'),
                'acquisition_cost': Decimal('28000000'),
                'appreciation_rate': Decimal('8.2'),
                'provenance': 'Durand-Ruel Gallery, Paris; Private collection, New York; Christie\'s New York, 2019',
                'image_url': '',
            },
            {
                'title': 'Bronze Reclining Figure',
                'description': 'A powerful bronze sculpture exemplifying Henry Moore\'s mastery of organic form. Cast from the original maquette, this piece shows the artist\'s signature exploration of the human form in landscape.',
                'category': 'sculpture',
                'status': 'active',
                'artist_name': 'Henry Moore',
                'medium': 'Bronze, edition of 6',
                'origin_country': 'United Kingdom',
                'year_created': '1969',
                'dimensions': '92 x 244 x 112 cm',
                'estimated_value': Decimal('6800000'),
                'acquisition_cost': Decimal('5400000'),
                'appreciation_rate': Decimal('9.8'),
                'provenance': 'Henry Moore Foundation; Marlborough Gallery; Private collection, Geneva',
                'image_url': '',
            },
            {
                'title': 'Self Portrait with Thorn Necklace',
                'description': 'A stunning reproduction-quality painting in the style of Frida Kahlo\'s iconic self-portraits, created by a contemporary Mexican artist working in the tradition. Powerful symbolism and vivid color palette.',
                'category': 'painting',
                'status': 'active',
                'artist_name': 'Maria Izquierdo',
                'medium': 'Oil on Masonite',
                'origin_country': 'Mexico',
                'year_created': '1948',
                'dimensions': '61 x 47 cm',
                'estimated_value': Decimal('1200000'),
                'acquisition_cost': Decimal('950000'),
                'appreciation_rate': Decimal('13.1'),
                'provenance': 'Private collection, Mexico City; Sotheby\'s New York, 2021',
                'image_url': '',
            },
            {
                'title': 'Electric Chair (Sunday B. Morning)',
                'description': 'A powerful screen print from Andy Warhol\'s Electric Chair series, exploring themes of mortality and media in America. Authenticated and in excellent condition.',
                'category': 'print_art',
                'status': 'active',
                'artist_name': 'Andy Warhol',
                'medium': 'Screenprint on paper',
                'origin_country': 'United States',
                'year_created': '1971',
                'dimensions': '90 x 122 cm',
                'estimated_value': Decimal('1800000'),
                'acquisition_cost': Decimal('1400000'),
                'appreciation_rate': Decimal('10.9'),
                'provenance': 'Leo Castelli Gallery; Private collection, New York; Phillips New York, 2022',
                'image_url': '',
            },
        ]

        for data in artworks_data:
            artwork = Artwork(artist_id=artist_user.id, **data)
            db.add(artwork)

        db.commit()

        # Create investment opportunities for active artworks
        artworks = db.query(Artwork).filter(Artwork.status == 'active').all()
        risk_levels = [RiskLevel.A, RiskLevel.B, RiskLevel.B, RiskLevel.A, RiskLevel.C,
                       RiskLevel.B, RiskLevel.A, RiskLevel.B, RiskLevel.B]
        funding_types = ['fractional_ownership', 'fractional_ownership', 'fractional_ownership',
                         'fractional_ownership', 'fractional_ownership', 'fractional_ownership',
                         'art_backed_lending', 'fractional_ownership', 'fractional_ownership']

        for i, artwork in enumerate(artworks):
            goal = float(artwork.acquisition_cost or artwork.estimated_value or 100000)
            raised_pct = [0.72, 0.45, 0.88, 0.33, 0.95, 0.61, 0.15, 0.50, 0.78][i % 9]
            opp = InvestmentOpportunity(
                artwork_id=artwork.id,
                name=f'Invest in: {artwork.title}',
                description=f'Fractional ownership opportunity in "{artwork.title}" by {artwork.artist_name}. '
                           f'Estimated current value: ${artwork.estimated_value:,.0f}. '
                           f'Historical appreciation rate: {artwork.appreciation_rate}% annually.',
                funding_goal=Decimal(str(goal)),
                amount_raised=Decimal(str(round(goal * raised_pct, 2))),
                minimum_investment=Decimal('500'),
                interest_rate=artwork.appreciation_rate or Decimal('12.0'),
                term_months=[60, 84, 48, 72, 36, 60, 24, 48, 60][i % 9],
                start_date=date(2025, 1 + (i % 12), 1),
                end_date=date(2026, 6, 30),
                funding_status='open',
                risk_level=risk_levels[i % 9].value,
                funding_type=funding_types[i % 9],
            )
            db.add(opp)

        # Create funded opportunity for the Monet
        monet = db.query(Artwork).filter(Artwork.title.like('%Water Lilies%')).first()
        if monet:
            opp = InvestmentOpportunity(
                artwork_id=monet.id,
                name=f'Invest in: {monet.title}',
                description=f'Fully funded fractional ownership in "{monet.title}" by {monet.artist_name}.',
                funding_goal=Decimal('28000000'),
                amount_raised=Decimal('28000000'),
                minimum_investment=Decimal('1000'),
                interest_rate=Decimal('8.2'),
                term_months=120,
                start_date=date(2024, 3, 1),
                end_date=date(2034, 3, 1),
                funding_status='funded',
                risk_level='A',
                funding_type='fractional_ownership',
            )
            db.add(opp)

        # Seed some FAQs
        faqs = [
            ('What is Kanvas.ai?', 'Kanvas.ai is a fine art investment platform that allows you to buy fractional shares of museum-quality artworks. We handle authentication, storage, insurance, and eventual sale of the artworks.'),
            ('How does fractional art ownership work?', 'We acquire blue-chip artworks, securitize them into shares, and offer fractional ownership to our investors. When an artwork is sold, investors receive their proportional share of the proceeds.'),
            ('What is the minimum investment?', 'The minimum investment varies by offering but typically starts at $500. Some higher-value works may have higher minimums.'),
            ('How are artworks valued?', 'All artworks are independently appraised by certified appraisers using auction records, private sale comparables, and current market conditions. Valuations are updated periodically.'),
            ('Where are the artworks stored?', 'All artworks are stored in museum-grade, climate-controlled facilities with 24/7 security, fire suppression, and comprehensive insurance coverage.'),
            ('Can I sell my shares before the artwork is sold?', 'Yes, you can trade your fractional positions on our secondary market at any time, subject to available liquidity.'),
            ('What are the typical returns?', 'Historical returns vary by artwork, but blue-chip art has appreciated at approximately 13.8% annually over the past 25 years. Past performance does not guarantee future results.'),
            ('Is my investment insured?', 'Yes, all artworks on our platform are fully insured against damage, theft, and loss. Insurance costs are included in the management fee.'),
        ]
        for i, (q, a) in enumerate(faqs):
            existing = db.query(FAQ).filter(FAQ.question == q).first()
            if not existing:
                db.add(FAQ(question=q, answer=a, display_order=i, is_active=True))

        db.commit()
        print(f"Seeded {len(artworks_data)} artworks, investment opportunities, and FAQs.")

    finally:
        db.close()


if __name__ == '__main__':
    seed()
