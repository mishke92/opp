import pytest
from app.models import User
from app import db as database # Use a different alias to avoid conflict with 'db' fixture

def test_register_new_user(client, db):
    response = client.post('/register', data={
        'nombre': 'New User',
        'email': 'newuser@example.com',
        'password': 'newpassword123',
        'idioma_preferido': 'es',
        'pais_interes': 'EC',
        'accept_privacy': 'true',
        'accept_terms': 'true'
    }, follow_redirects=True)
    assert response.status_code == 200 # Should redirect to login, then 200
    assert b'Felicidades, ahora eres un usuario registrado!' in response.data # Flash message

    user = User.query.filter_by(email='newuser@example.com').first()
    assert user is not None
    assert user.nombre == 'New User'

def test_register_existing_user(client, db):
    # First, create a user
    user = User(email='existing@example.com', nombre='Existing User')
    user.set_password('password123')
    database.session.add(user)
    database.session.commit()

    response = client.post('/register', data={
        'nombre': 'Another User',
        'email': 'existing@example.com', # Same email
        'password': 'anotherpassword',
        'idioma_preferido': 'en',
        'pais_interes': 'CO',
        'accept_privacy': 'true',
        'accept_terms': 'true'
    })
    assert response.status_code == 200 # Stays on registration page
    assert b'La direcci\xc3\xb3n de correo electr\xc3\xb3nico ya est\xc3\xa1 registrada.' in response.data # Flash message (UTF-8 encoded)

def test_login_valid_credentials(client, db):
    user = User(email='loginuser@example.com', nombre='Login User')
    user.set_password('loginpass')
    database.session.add(user)
    database.session.commit()

    response = client.post('/login', data={
        'email': 'loginuser@example.com',
        'password': 'loginpass'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome back, Login User!' in response.data
    with client.session_transaction() as sess:
        assert sess['user_id'] == user.id

def test_login_invalid_email(client, db):
    response = client.post('/login', data={
        'email': 'nonexistent@example.com',
        'password': 'somepassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid email or password.' in response.data
    with client.session_transaction() as sess:
        assert 'user_id' not in sess

def test_login_invalid_password(client, db):
    user = User(email='loginuser2@example.com', nombre='Login User 2')
    user.set_password('correctpass')
    database.session.add(user)
    database.session.commit()

    response = client.post('/login', data={
        'email': 'loginuser2@example.com',
        'password': 'wrongpassword'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Invalid email or password.' in response.data
    with client.session_transaction() as sess:
        assert 'user_id' not in sess

def test_logout(client, db):
    # First, log in a user
    user = User(email='logoutuser@example.com', nombre='Logout User')
    user.set_password('logoutpass')
    database.session.add(user)
    database.session.commit()
    client.post('/login', data={'email': 'logoutuser@example.com', 'password': 'logoutpass'})

    response = client.get('/logout', follow_redirects=True)
    assert response.status_code == 200
    assert b'You have been logged out.' in response.data
    with client.session_transaction() as sess:
        assert 'user_id' not in sess
        assert 'guest_mode' not in sess # Ensure guest mode is also cleared if it was set

def test_access_protected_route_unauthenticated(client, db):
    response = client.get('/mi_perfil', follow_redirects=True)
    assert response.status_code == 200 # Redirects to login
    # Corrected flash message based on /mi_perfil route's specific message
    assert b'Debes iniciar sesi\xc3\xb3n para ver tu perfil.' in response.data
    assert request.path == '/login' # Check final path is login

def test_guest_login(client, db):
    response = client.get('/guest_login', follow_redirects=True)
    assert response.status_code == 200
    assert b'You are now browsing as a guest.' in response.data
    with client.session_transaction() as sess:
        assert sess['guest_mode'] is True
        assert 'user_id' not in sess

def test_register_missing_terms_acceptance(client, db):
    response = client.post('/register', data={
        'nombre': 'No Terms User',
        'email': 'noterms@example.com',
        'password': 'password123',
        'idioma_preferido': 'es',
        'pais_interes': 'EC',
        # Missing accept_privacy and accept_terms
    })
    assert response.status_code == 200
    assert b'Debe aceptar la Pol\xc3\xadtica de Privacidad y los T\xc3\xa9rminos de Servicio para registrarse.' in response.data
    user = User.query.filter_by(email='noterms@example.com').first()
    assert user is None # User should not be created
