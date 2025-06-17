import pytest
import sys
import os

# Add project root to sys.path to allow imports from 'app'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db as _db
from app.config import TestingConfig
# from seed_data import seed_all # Optional: if you want to seed data for all tests

@pytest.fixture(scope='session')
def app():
    """Session-wide test `Flask` application."""
    app_instance = create_app(config_class=TestingConfig)

    # Establish an application context before running the tests.
    # app_context = app_instance.app_context()
    # app_context.push()

    # # Ensure DB is created (if not handled by db fixture's session scope)
    # with app_instance.app_context():
    #    _db.create_all()

    # yield app_instance

    # # Clean up
    # with app_instance.app_context():
    #    _db.drop_all()
    # app_context.pop()
    return app_instance


@pytest.fixture(scope='function') # 'function' scope for client to ensure isolation
def client(app):
    """A test client for the app."""
    with app.test_client() as test_client:
        with app.app_context(): # Ensure app context is active for client usage
            yield test_client


@pytest.fixture(scope='session')
def db_instance_for_session(app):
    """
    Returns a SQLAlchemy database instance for the session.
    This allows tests to use the same database session.
    """
    with app.app_context():
        # _db.drop_all() # Ensure clean state if reusing a file-based DB
        _db.create_all()
        yield _db
        _db.session.remove() # Clean up session
        _db.drop_all()       # Drop all tables after test session


@pytest.fixture(scope='function')
def db(db_instance_for_session, app):
    """
    Provides a transactional scope for tests. Rolls back changes after each test.
    This uses the session-scoped db_instance_for_session for table creation/dropping.
    """
    connection = db_instance_for_session.engine.connect()
    transaction = connection.begin()

    db_instance_for_session.session.begin_nested() # Use savepoints

    # Monkeypatch the session object on the db_instance_for_session to use this transaction
    # This is a bit of a hack, but ensures that db.session within tests uses this transaction
    # A more robust way might involve a session manager or scoped_session if issues arise.

    # For now, we'll rely on tests using db.session.add/commit and then rolling back the outer transaction.
    # Tests should ideally use db.session directly from this fixture.

    yield db_instance_for_session

    # Rollback the nested transaction (savepoint)
    db_instance_for_session.session.rollback()
    # Rollback the outer transaction
    transaction.rollback()
    connection.close()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()

# Optional: Fixture to seed data for specific tests if needed
# @pytest.fixture(scope='function')
# def seed(db):
#     """Seeds the database for a test."""
#     # Call your seeding functions here, e.g., from seed_data.py
#     # from seed_data import seed_users, seed_countries # etc.
#     # seed_countries()
#     # seed_users()
#     # ...
#     # db.session.commit() # Commit after seeding
#     pass
