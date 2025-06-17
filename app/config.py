import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:password@localhost/legal_app_db' # Default for base Config
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///:memory:' # Use in-memory SQLite for tests
    WTF_CSRF_ENABLED = False # Disable CSRF forms for easier testing
    LOGIN_DISABLED = False # Ensure login/auth is active for tests
    # Using a separate secret key for testing is a good practice if needed,
    # but can also inherit from Config. For simplicity, we'll inherit.
    # SERVER_NAME might be needed for url_for to work correctly in some test contexts
    # if app context isn't fully set up by pytest-flask in a specific way.
    # For now, we assume pytest-flask handles app context sufficiently.

class DevelopmentConfig(Config):
    DEBUG = True
    # Example: Use a local PostgreSQL DB for development if available, else SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'dev.db') # Store in project root
    # Or keep it simple for now and inherit the default PostgreSQL from Config if that's used for dev:
    # SQLALCHEMY_DATABASE_URI = Config.SQLALCHEMY_DATABASE_URI


class ProductionConfig(Config):
    DEBUG = False
    # SECRET_KEY should be set in environment for production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    # DATABASE_URL should be set in environment for production
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    # Example: Logging configuration for production
    # import logging
    # from logging.handlers import RotatingFileHandler
    # file_handler = RotatingFileHandler('error.log', maxBytes=1024 * 1024 * 100, backupCount=20)
    # file_handler.setLevel(logging.ERROR)
    # formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # file_handler.setFormatter(formatter)
    # # Add more handlers as needed (e.g., for INFO level)
    # # app.logger.addHandler(file_handler) # Would need app instance here, usually done in create_app

    # Ensure critical environment variables are checked at startup if not provided
    # This can be done in create_app or wsgi.py
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set for production app")
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("No DATABASE_URL set for production app")
