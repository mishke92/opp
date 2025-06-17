from app import db, create_app
from app.models import Country, User, LawyerProfile, Law, LegalTerm, Article, Event, Subscription # Added Subscription
from datetime import datetime, timedelta

def seed_countries():
    if Country.query.filter_by(code='EC').first():
        print("Ecuador already exists.")
        return Country.query.filter_by(code='EC').first()

    ecuador = Country(name='Ecuador', code='EC')
    db.session.add(ecuador)
    db.session.commit()
    print("Ecuador seeded.")
    return ecuador

def seed_users():
    if User.query.filter_by(email='testuser1@example.com').first():
        print("Test users already exist.")
        return

    user1 = User(email='testuser1@example.com', nombre='Usuario Uno Gratuito', idioma_preferido='es', pais_interes='Ecuador')
    user1.set_password('password123')

    user2 = User(email='testuser2@example.com', nombre='Usuario Dos Gratuito', idioma_preferido='es', pais_interes='Ecuador')
    user2.set_password('password456')

    # User 1 will be made premium via a subscription record later in seed_subscriptions()
    # user1.tipo_suscripcion = 'premium'

    user_lawyer1 = User(email='lawyer1@example.com', nombre='Abogado Uno', idioma_preferido='es', pais_interes='Ecuador')
    user_lawyer1.set_password('lawyerpass1')

    user_lawyer2 = User(email='lawyer2@example.com', nombre='Abogada Dos', idioma_preferido='es', pais_interes='Ecuador')
    user_lawyer2.set_password('lawyerpass2')

    admin_user = User(
        email='admin@example.com',
        nombre='Admin User',
        idioma_preferido='es',
        pais_interes='Ecuador', # Default country
        is_admin=True
    )
    admin_user.set_password('adminpass')

    db.session.add_all([user1, user2, user_lawyer1, user_lawyer2, admin_user])
    db.session.commit()
    print("Users seeded (including admin).")

def seed_lawyer_profiles(country_ec):
    if LawyerProfile.query.count() > 0:
        print("Lawyer profiles already exist.")
        return

    lawyer_user1 = User.query.filter_by(email='lawyer1@example.com').first()
    lawyer_user2 = User.query.filter_by(email='lawyer2@example.com').first()

    if not lawyer_user1 or not lawyer_user2:
        print("Lawyer users not found, please seed users first.")
        return

    profile1 = LawyerProfile(
        user_id=lawyer_user1.id,
        country_id=country_ec.id,
        specialization='Derecho Penal',
        bio='Abogado con 5 años de experiencia en litigios penales.',
        contact_info='penal1@example.com',
        is_premium_profile=True, # Make this one premium
        full_bio='Con una trayectoria destacada en la defensa de casos complejos, el Abogado Uno ofrece una representación legal integral. Su práctica se enfoca en la justicia penal, garantizando los derechos de sus clientes en todas las etapas del proceso. Ha participado en numerosos juicios orales y posee un profundo conocimiento del sistema judicial ecuatoriano. Adicionalmente, es autor de varias publicaciones en revistas especializadas y ponente en seminarios sobre reforma procesal penal.',
        direct_phone='0991234567 (Solo Premium)'
    )
    profile2 = LawyerProfile(
        user_id=lawyer_user2.id,
        country_id=country_ec.id,
        specialization='Derecho Civil',
        bio='Especialista en contratos y derecho de familia.',
        contact_info='civil2@example.com',
        is_premium_profile=False, # This one remains non-premium
        full_bio='La Abogada Dos es una reconocida experta en el ámbito del derecho civil, con particular énfasis en la resolución de disputas contractuales y asuntos de familia. Su enfoque se centra en encontrar soluciones eficientes y justas para sus clientes, priorizando la mediación y el acuerdo cuando es posible. Cuenta con una maestría en Derecho Procesal y es miembro activo de varias asociaciones profesionales.',
        direct_phone='0987654321 (Solo Premium, si fuera premium)'
    )
    db.session.add_all([profile1, profile2])
    db.session.commit()
    print("Lawyer profiles seeded.")


def seed_laws(country_ec):
    if Law.query.count() > 0:
        print("Laws already exist.")
        return
    law1 = Law(
        country_id=country_ec.id,
        title='Constitución de la República del Ecuador',
        content_summary='Resumen de la Constitución de Montecristi de 2008, enfocada en derechos y organización del estado.',
        full_content_path='Texto completo de la Constitución de la República del Ecuador... (versión premium con análisis y concordancias)... Artículo 1: El Ecuador es un Estado constitucional de derechos y justicia, social, democrático, soberano, independiente, unitario, intercultural, plurinacional y laico. Se organiza en forma de república y se gobierna de manera descentralizada. (Este es un ejemplo, el contenido real sería mucho más largo y formateado).',
        category='Constitucional',
        published_date=datetime(2008, 10, 20)
    )
    law2 = Law(
        country_id=country_ec.id,
        title='Código Orgánico General de Procesos (COGEP)',
        content_summary='Regula los procesos judiciales en materias no penales en Ecuador.',
        full_content_path='Texto completo del COGEP... (versión premium con comentarios y jurisprudencia asociada)... TÍTULO PRELIMINAR: ÁMBITO Y PRINCIPIOS. Artículo 1.- Ámbito. Este Código regula la actividad procesal en todas las materias, excepto la constitucional, electoral y penal. (Ejemplo).',
        category='Procesal Civil',
        published_date=datetime(2015, 5, 22)
    )
    law3 = Law(
        country_id=country_ec.id,
        title='Ley Orgánica de Protección de Datos Personales',
        content_summary='Establece el marco para la protección de datos personales en Ecuador.',
        full_content_path='#limited',
        category='Protección de Datos',
        published_date=datetime(2021, 5, 26)
    )
    db.session.add_all([law1, law2, law3])
    db.session.commit()
    print("Laws seeded.")

def seed_legal_terms(country_ec):
    if LegalTerm.query.count() > 0:
        print("Legal terms already exist.")
        return
    term1 = LegalTerm(country_id=country_ec.id, term='Habeas Corpus', definition='Garantía constitucional que protege la libertad individual contra detenciones arbitrarias.')
    term2 = LegalTerm(country_id=country_ec.id, term='Recurso de Casación', definition='Medio de impugnación extraordinario para anular una sentencia judicial que contiene una incorrecta interpretación o aplicación de la ley.')
    term3 = LegalTerm(country_id=country_ec.id, term='Jurisdicción Contencioso-Administrativa', definition='Ámbito de la justicia encargado de resolver conflictos entre la administración pública y los ciudadanos.')
    term4 = LegalTerm(country_id=country_ec.id, term='Debido Proceso', definition='Conjunto de garantías procesales que deben respetarse para asegurar un juicio justo.')
    db.session.add_all([term1, term2, term3, term4])
    db.session.commit()
    print("Legal terms seeded.")

def seed_articles(country_ec):
    if Article.query.count() > 0:
        print("Articles already exist.")
        return

    author1 = User.query.filter_by(email='lawyer1@example.com').first()

    article1 = Article(
        country_id=country_ec.id,
        title='Análisis de la Ley de Protección de Datos en Ecuador',
        content_preview='La nueva Ley Orgánica de Protección de Datos Personales presenta desafíos y oportunidades para las empresas en Ecuador...',
        full_content_path='Contenido completo del Artículo 1: La Ley Orgánica de Protección de Datos Personales tiene como objetivo garantizar el derecho a la protección de datos personales, incluyendo el acceso y la decisión sobre información y datos de este carácter, así como su correspondiente protección. Para ello, regula su tratamiento legítimo, informado, específico y leal, en el marco del respeto a los derechos fundamentales y libertades públicas de los ciudadanos y residentes en Ecuador. (Este es un ejemplo de contenido extendido para premium).',
        author_id=author1.id if author1 else None,
        published_date=datetime.utcnow() - timedelta(days=10)
    )
    article2 = Article(
        country_id=country_ec.id,
        title='Implicaciones del COGEP en los Litigios Civiles',
        content_preview='El Código Orgánico General de Procesos ha transformado la manera de llevar los juicios civiles en el país, enfocándose en la oralidad...',
        full_content_path='Contenido completo del Artículo 2: El COGEP busca modernizar la administración de justicia civil en Ecuador, introduciendo principios como la inmediación, concentración y celeridad procesal. Este artículo explora en detalle las principales innovaciones, como las audiencias orales, la carga probatoria y los nuevos recursos. (Ejemplo de contenido extendido).',
        author_id=author1.id if author1 else None,
        published_date=datetime.utcnow() - timedelta(days=5)
    )
    db.session.add_all([article1, article2])
    db.session.commit()
    print("Articles seeded.")

def seed_events(country_ec):
    if Event.query.count() > 0:
        print("Events already exist.")
        return
    event1 = Event(
        country_id=country_ec.id,
        title='Conferencia: El Futuro del Derecho Digital en Ecuador',
        description='Panel de discusión sobre los retos de la legislación en la era digital. Temas: IA, protección de datos, cibercrimen.',
        event_date=datetime.utcnow() + timedelta(days=30),
        location='Quito, Centro de Convenciones',
        is_premium_content=False,
        exclusive_content_details='Acceso a las grabaciones de todas las ponencias, material de presentación y un foro privado con los panelistas durante una semana después del evento.'
    )
    event2 = Event(
        country_id=country_ec.id,
        title='Taller Práctico: Aplicación del COGEP',
        description='Jornada intensiva para abogados sobre técnicas de litigación oral bajo el COGEP.',
        event_date=datetime.utcnow() + timedelta(days=45),
        location='Guayaquil, Hotel Hilton Colón',
        is_premium_content=False # This is a free event for the list
    )
    event3 = Event(
        country_id=country_ec.id,
        title='Seminario Exclusivo: Inversión Extranjera y Arbitraje Internacional',
        description='Análisis profundo de los mecanismos de protección de inversiones y resolución de disputas.',
        event_date=datetime.utcnow() + timedelta(days=60),
        location='Online (Premium Access)',
        is_premium_content=True,
        exclusive_content_details='Este seminario incluye sesiones de Q&A en vivo con expertos internacionales, estudios de caso detallados, y acceso a una biblioteca de recursos sobre arbitraje y tratados bilaterales de inversión. Se entregarán certificados de participación.'
    )
    db.session.add_all([event1, event2, event3])
    db.session.commit()
    print("Events seeded.")

def seed_all():
    app = create_app()
    with app.app_context():
        # Ensure tables are created for a fresh setup if not using migrations to create them first
        # In a typical workflow, migrations would handle table creation.
        # This is a fallback for a simple seed script.
        try:
            # Check if a known table exists, e.g., 'country'
            # This is a simplistic check. A more robust check might be needed.
            with db.engine.connect() as connection:
                result = connection.execute(db.text("SELECT 1 FROM country LIMIT 1"))
                result.fetchone()
            print("Tables seem to exist. Skipping db.create_all().")
        except Exception as e:
            print(f"Tables might not exist (error: {e}). Running db.create_all()...")
            db.create_all()
            print("db.create_all() executed.")

        print("Starting data seeding...")
        country_ec = seed_countries()
        if country_ec:
            seed_users() # Seed users first as other models might depend on them
            seed_lawyer_profiles(country_ec)
            seed_laws(country_ec)
            seed_legal_terms(country_ec)
            seed_articles(country_ec) # Articles can have authors (Users)
            seed_events(country_ec)
            seed_subscriptions() # Seed subscriptions after users
        else:
            print("Seeding aborted as Ecuador country was not found or created.")
        print("Data seeding finished.")

def seed_subscriptions():
    if Subscription.query.count() > 0:
        print("Subscriptions already exist.")
        return

    user1 = User.query.filter_by(email='testuser1@example.com').first()
    if not user1:
        print("User testuser1@example.com not found for seeding subscription.")
        return

    # Make user1 premium
    premium_subscription = Subscription(
        user_id=user1.id,
        subscription_type='premium', # Corrected field name
        start_date=datetime.utcnow() - timedelta(days=5), # Started 5 days ago
        end_date=datetime.utcnow() + timedelta(days=25),  # Ends in 25 days
        status='active'
    )
    db.session.add(premium_subscription)

    # Also update the user's direct field for quick checks, if still used
    user1.tipo_suscripcion = 'premium'
    db.session.add(user1)

    db.session.commit()
    print("Subscriptions seeded (user1 is now premium).")


if __name__ == '__main__':
    # This allows running `python seed_data.py`
    # Ensure your Flask app's configuration (especially DB URI) is accessible
    # e.g. through environment variables if run standalone.
    # For simplicity in this environment, it's better to run this via flask shell or a custom command.
    print("To seed data, run the following commands in 'flask shell':")
    print("from seed_data import seed_all")
    print("seed_all()")
    # To make it directly executable (requires proper app context setup):
    # app = create_app()
    # with app.app_context():
    #     db.create_all() # Ensure tables are created if they aren't
    #     seed_all()
