from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from .config import Config

db = SQLAlchemy()
migrate = Migrate()

# Import config classes
from .config import Config, DevelopmentConfig, TestingConfig, ProductionConfig

config_by_name = dict(
    development=DevelopmentConfig,
    testing=TestingConfig,
    production=ProductionConfig,
    default=DevelopmentConfig # Default if FLASK_CONFIG is not set or unrecognized
)

def create_app(config_name_or_class='default'):
    app = Flask(__name__)

    if isinstance(config_name_or_class, str):
        config_obj = config_by_name.get(config_name_or_class.lower(), config_by_name['default'])
    else: # Assume it's a class object
        config_obj = config_name_or_class

    app.config.from_object(config_obj)

    # Ensure SECRET_KEY and DATABASE_URL are checked if in production context
    # This is a safeguard, as ProductionConfig itself raises errors if they are not set.
    if app.config.get('ENV') == 'production': # FLASK_ENV is 'production' when DEBUG=False
        if not app.config.get('SECRET_KEY') or \
           not app.config.get('SQLALCHEMY_DATABASE_URI') or \
           app.config.get('SECRET_KEY') == 'you-will-never-guess': # Default from base Config
            # This check might be redundant if ProductionConfig already raises an error.
            # However, it can catch cases where ProductionConfig might not be used as expected.
            print("WARNING: Production environment variables may not be properly set. Check SECRET_KEY and DATABASE_URL.")


    db.init_app(app)
    migrate.init_app(app, db)

    # Register blueprints here
    # from .main import bp as main_bp
    # app.register_blueprint(main_bp)

    # from .auth import bp as auth_bp
    # app.register_blueprint(auth_bp, url_prefix='/auth')

    from app import models # Import models here
    from app.routes import register_routes
    register_routes(app) # Register routes

    # Flask-Admin setup
    from app.admin import init_admin
    models_to_register_in_admin = [
        (models.Country, 'Países'),
        (models.Law, 'Leyes'),
        (models.LegalTerm, 'Términos Legales'),
        (models.Article, 'Artículos'),
        (models.Event, 'Eventos'),
        (models.LawyerProfile, 'Perfiles de Abogados'),
        (models.Subscription, 'Suscripciones') # Already has custom view in admin.py
        # User is added with a custom view directly in admin.py
    ]
    init_admin(app, db, *models_to_register_in_admin)

    return app
