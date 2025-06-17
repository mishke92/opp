import pytest
from app.models import User, Subscription
from datetime import datetime, timedelta

def test_user_password_hashing(db):
    u = User(email='test@example.com', nombre='Test User')
    u.set_password('cat')
    assert u.password_hash != 'cat'
    assert u.check_password('cat')
    assert not u.check_password('dog')

def test_user_repr(db):
    u = User(email='test@example.com', nombre='Test User')
    db.session.add(u)
    db.session.commit()
    assert repr(u) == '<User test@example.com>'

def test_has_active_premium_subscription_no_subscription(db):
    user = User(email='free@example.com', nombre='Free User')
    db.session.add(user)
    db.session.commit()
    assert not user.has_active_premium_subscription()

def test_has_active_premium_subscription_active_premium(db):
    user = User(email='premium@example.com', nombre='Premium User', tipo_suscripcion='premium')
    db.session.add(user)
    db.session.commit() # Commit user to get user.id

    sub = Subscription(
        user_id=user.id,
        subscription_type='premium',
        status='active',
        start_date=datetime.utcnow() - timedelta(days=10),
        end_date=datetime.utcnow() + timedelta(days=20)
    )
    db.session.add(sub)
    db.session.commit()
    assert user.has_active_premium_subscription()

def test_has_active_premium_subscription_expired_premium(db):
    user = User(email='expired@example.com', nombre='Expired Premium', tipo_suscripcion='free') # tipo_suscripcion should reflect current state
    db.session.add(user)
    db.session.commit()

    sub = Subscription(
        user_id=user.id,
        subscription_type='premium',
        status='expired', # Or 'active' but with end_date in the past
        start_date=datetime.utcnow() - timedelta(days=30),
        end_date=datetime.utcnow() - timedelta(days=1)
    )
    db.session.add(sub)
    db.session.commit()
    assert not user.has_active_premium_subscription()

def test_has_active_premium_subscription_cancelled_premium(db):
    user = User(email='cancelled@example.com', nombre='Cancelled Premium', tipo_suscripcion='free')
    db.session.add(user)
    db.session.commit()

    sub = Subscription(
        user_id=user.id,
        subscription_type='premium',
        status='cancelled',
        start_date=datetime.utcnow() - timedelta(days=10),
        end_date=datetime.utcnow() + timedelta(days=20) # Still within date range, but cancelled
    )
    db.session.add(sub)
    db.session.commit()
    assert not user.has_active_premium_subscription()

def test_has_active_premium_subscription_free_subscription(db):
    user = User(email='onlyfree@example.com', nombre='Only Free Sub', tipo_suscripcion='free')
    db.session.add(user)
    db.session.commit()

    sub = Subscription(
        user_id=user.id,
        subscription_type='free',
        status='active',
        start_date=datetime.utcnow() - timedelta(days=10),
        end_date=None # Free might not expire or have a very long end date
    )
    db.session.add(sub)
    db.session.commit()
    assert not user.has_active_premium_subscription()

def test_has_active_premium_subscription_none_end_date(db):
    user = User(email='premium_forever@example.com', nombre='Premium Forever', tipo_suscripcion='premium')
    db.session.add(user)
    db.session.commit()

    sub = Subscription(
        user_id=user.id,
        subscription_type='premium',
        status='active',
        start_date=datetime.utcnow() - timedelta(days=10),
        end_date=None # Perpetual premium
    )
    db.session.add(sub)
    db.session.commit()
    assert user.has_active_premium_subscription()

def test_user_is_admin_property(db):
    admin_user = User(email='admin@example.com', nombre='Admin', is_admin=True)
    regular_user = User(email='user@example.com', nombre='Regular', is_admin=False)
    db.session.add_all([admin_user, regular_user])
    db.session.commit()
    assert admin_user.is_admin
    assert not regular_user.is_admin

def test_user_is_authenticated_property(db):
    # This property is currently hardcoded to True for any User object
    # In a real Flask-Login setup, it would depend on login state.
    user = User(email='anyuser@example.com', nombre='Any User')
    db.session.add(user)
    db.session.commit()
    assert user.is_authenticated

# Add more model tests if other models have significant custom logic.
# For example, testing relationships or custom methods on Law, Article, etc.
# For now, focusing on User as it has the most custom logic.
