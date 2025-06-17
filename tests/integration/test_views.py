import pytest
from app.models import User, Country, Subscription, Law
from app import db as database # Use a different alias
from datetime import datetime, timedelta
from flask import request, session # Added session to this import line

# Helper function to log in a user
def login_user(client, email, password):
    return client.post('/login', data={'email': email, 'password': password}, follow_redirects=True)

# Helper function to create a user
def create_user(email, password, nombre="Test User", is_admin=False, tipo_suscripcion='free'):
    user = User(email=email, nombre=nombre, is_admin=is_admin, tipo_suscripcion=tipo_suscripcion)
    user.set_password(password)
    database.session.add(user)
    # database.session.commit() # Avoid commit here, let test fixture handle transaction
    database.session.flush() # Ensure user.id is available if needed later in the same setup
    return user

def create_premium_user(email, password, nombre="Premium User"):
    user = create_user(email, password, nombre, tipo_suscripcion='premium') # Will set tipo_suscripcion directly
    # Create an active premium subscription for this user
    sub = Subscription(
        user_id=user.id, # user.id should be available due to flush in create_user
        subscription_type='premium',
        status='active',
        start_date=datetime.utcnow() - timedelta(days=1),
        end_date=datetime.utcnow() + timedelta(days=29)
    )
    database.session.add(sub)
    # database.session.commit() # Avoid commit
    database.session.flush()
    return user

def create_admin_user(email, password, nombre="Admin User"):
    return create_user(email, password, nombre, is_admin=True)


def test_home_page_anonymous(client, db):
    response = client.get('/')
    assert response.status_code == 200
    assert b"Bienvenido al Consultorio Jur\xc3\xaddico" in response.data

def test_leyes_page_anonymous(client, db):
    # Need to ensure Ecuador exists for these tests
    ecuador = Country.query.filter_by(code='EC').first()
    if not ecuador:
        ecuador = Country(name='Ecuador', code='EC')
        database.session.add(ecuador)
        database.session.flush() # Use flush to get ID if needed by Law immediately

    law1 = Law(title="Ley Ejemplo", content_summary="Resumen...", country_id=ecuador.id, category="Civil")
    database.session.add(law1)
    database.session.flush() # Flush to ensure data is in session for query

    response = client.get('/leyes')
    assert response.status_code == 200
    assert b"Leyes de Ecuador" in response.data
    assert b"Resumen de la legislaci\xc3\xb3n ecuatoriana." in response.data # Free tier text
    assert b"Actualizar a Premium" in response.data # Premium promo

def test_leyes_page_premium_user(client, db):
    ecuador = Country.query.filter_by(code='EC').first()
    if not ecuador:
        ecuador = Country(name='Ecuador', code='EC')
        database.session.add(ecuador)
        database.session.flush()

    law1 = Law(title="Ley Ejemplo Premium",
               content_summary="Resumen...",
               full_content_path="Contenido completo para premium...",
               country_id=ecuador.id, category="PremiumCat")
    database.session.add(law1)
    database.session.flush()

    create_premium_user('premium_leyes@example.com', 'password')
    login_user(client, 'premium_leyes@example.com', 'password')

    response = client.get('/leyes')
    assert response.status_code == 200
    assert b"Leyes de Ecuador" in response.data
    assert b"Contenido completo para premium..." in response.data
    assert b"Actualizar a Premium" not in response.data # No promo for premium
    assert b"Buscar por palabra clave..." in response.data # Search form

def test_subscription_flow(client, db):
    user = create_user('subtest@example.com', 'password', nombre='Sub Test User')
    login_user(client, 'subtest@example.com', 'password')

    # Go to plans page
    response = client.get('/planes')
    assert response.status_code == 200
    assert b"Actualizar a Premium" in response.data

    # Simulate subscribing
    response = client.post('/subscribe/premium', follow_redirects=True)
    assert response.status_code == 200 # Redirects to profile
    assert b"Mi Perfil" in response.data # On profile page
    assert b"Ahora tienes una suscripci\xc3\xb3n Premium activa" in response.data # Flash message

    updated_user = database.session.get(User, user.id) # Use db.session.get()
    assert updated_user.has_active_premium_subscription()
    # tipo_suscripcion is also updated in the route, check it
    assert updated_user.tipo_suscripcion == 'premium'

def test_admin_access_anonymous(client, db):
    response = client.get('/admin/', follow_redirects=True)
    assert response.status_code == 200 # Redirects to login
    assert b'Debes ser administrador para acceder a esta p\xc3\xa1gina.' in response.data # flash message
    assert request.path == '/login'

def test_admin_access_non_admin_user(client, db):
    create_user('nonadmin@example.com', 'password')
    login_user(client, 'nonadmin@example.com', 'password')

    response = client.get('/admin/', follow_redirects=True)
    assert response.status_code == 200 # Redirects to login, or shows error then redirects
    # Depending on exact inaccessible_callback, it might redirect to login or another page
    # For now, we check that the admin page content is not there if it doesn't redirect to login
    # A more specific check would be for the flash message and the final URL.
    assert b'Debes ser administrador para acceder a esta p\xc3\xa1gina.' in response.data
    # Check if it redirects to login or index (if already logged in but not admin)
    assert request.path == '/login' or request.path == '/'


def test_admin_access_admin_user(client, db):
    create_admin_user('trueadmin@example.com', 'password')
    login_user(client, 'trueadmin@example.com', 'password')

    response = client.get('/admin/')
    assert response.status_code == 200
    assert b"Consultorio Admin" in response.data # Admin dashboard title
    assert b"Usuarios" in response.data # One of the model views

# Example of testing a route with country code
def test_leyes_colombia(client, db):
    colombia = Country.query.filter_by(code='CO').first()
    if not colombia:
        colombia = Country(name='Colombia', code='CO')
        database.session.add(colombia)
        database.session.flush() # Ensure ID is available

    law_co = Law(title="Ley Colombiana Ejemplo", content_summary="Resumen CO...", country_id=colombia.id, category="Civil CO")
    database.session.add(law_co)
    database.session.flush()

    response = client.get('/leyes/CO')
    assert response.status_code == 200
    assert b"Leyes de Colombia" in response.data
    assert b"Ley Colombiana Ejemplo" in response.data
    assert b"Resumen CO..." in response.data

    # Ensure Ecuador content is not shown
    ecuador = Country.query.filter_by(code='EC').first() # Ensure it exists if not already
    if not ecuador:
        ecuador = Country(name='Ecuador', code='EC')
        database.session.add(ecuador)
        database.session.flush()

    law_ec = Law(title="Ley Ecuatoriana Ejemplo", content_summary="Resumen EC...", country_id=ecuador.id, category="Civil EC")
    database.session.add(law_ec)
    database.session.flush()

    response_co = client.get('/leyes/CO') # Re-fetch for colombia
    assert b"Ley Ecuatoriana Ejemplo" not in response_co.data

    response_ec = client.get('/leyes/EC')
    assert b"Leyes de Ecuador" in response_ec.data
    assert b"Ley Ecuatoriana Ejemplo" in response_ec.data
    assert b"Ley Colombiana Ejemplo" not in response_ec.data
