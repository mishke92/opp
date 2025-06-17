import os
from app import create_app

# Determine the configuration class to use.
# Prioritize FLASK_CONFIG env var, then default to 'production'.
# The create_app function in __init__.py needs to be able to handle string names for configs.
config_name = os.getenv('FLASK_CONFIG', 'production')
app = create_app(config_name)

if __name__ == "__main__":
    # This block is for direct execution (e.g., `python wsgi.py`)
    # which is typically for local development/testing, not how Gunicorn runs it.
    # Gunicorn will call the 'app' callable directly.
    # For local dev, you might want to use 'development' config if FLASK_CONFIG is not set.
    if config_name == 'production' and not os.getenv('FLASK_CONFIG'):
        print("Warning: Running wsgi.py directly, defaulting to production config.")
        print("For development, set FLASK_CONFIG=development or run via 'flask run'.")

    # Check if required production environment variables are set if running with production config.
    # This is a secondary check; primary checks are in ProductionConfig itself.
    if app.config.get('ENV') == 'production': # FLASK_ENV is set by Flask based on DEBUG
        if not app.config.get('SECRET_KEY') or \
           not app.config.get('SQLALCHEMY_DATABASE_URI') or \
           app.config.get('SECRET_KEY') == 'you-will-never-guess': # Default from Config class
            print("CRITICAL: Production environment variables (SECRET_KEY, DATABASE_URL) are not properly set.")
            print("Aborting direct run. Use Gunicorn or ensure environment variables are correctly passed.")
            # exit(1) # Optionally exit if run directly in prod mode with bad config

    # For running with `python wsgi.py`, it's often better to use Flask's built-in server
    # which respects FLASK_DEBUG from environment.
    # The app.run() here is a simple way but doesn't offer Gunicorn's robustness.
    # Gunicorn should be used for production.
    print(f"Attempting to run app with configuration: {config_name}")
    print(f"Debug mode: {app.debug}")
    app.run()
