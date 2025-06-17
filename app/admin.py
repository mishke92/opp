from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask import session, redirect, url_for, request, flash # Added flash
from app.models import User, Subscription, Country, Law, LegalTerm, Article, Event, LawyerProfile # Added all models used

# Placeholder for current_user logic if not using Flask-Login
# For this exercise, we'll rely on session['user_id'] and is_admin flag
# In a full app, Flask-Login's current_user would be ideal.

def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        from app import db # Import db instance here to avoid circular import at module level if not already
        return db.session.get(User, user_id) # Changed to db.session.get()
    return None

class AdminModelView(ModelView):
    def is_accessible(self):
        user = get_current_user()
        return user and user.is_authenticated and user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        user = get_current_user()
        if not (user and user.is_authenticated):
            # If user is not authenticated at all, redirect to login
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login', next=request.url))
        else:
            # If user is authenticated but not admin, redirect to index or show error
            flash('No tienes permisos de administrador para acceder a esta página.', 'danger')
            return redirect(url_for('index')) # Or a specific 'unauthorized' page

class UserModelView(AdminModelView):
    column_exclude_list = ['password_hash'] # Don't show password hash
    form_excluded_columns = ['password_hash'] # Don't include it in forms
    column_searchable_list = ['email', 'nombre']
    column_filters = ['is_admin', 'tipo_suscripcion', 'pais_interes', 'idioma_preferido']
    can_export = True

class SubscriptionModelView(AdminModelView):
    # Removed 'user.email' from searchable list for simplicity for now.
    # Searching related models requires more setup (e.g., column_joins or custom logic).
    column_searchable_list = ['subscription_type', 'status']
    column_filters = ['subscription_type', 'status', 'start_date', 'end_date', 'user_id'] # Added user_id for filtering
    can_export = True
    column_list = ('user_id', 'subscription_type', 'start_date', 'end_date', 'status') # Explicitly list columns
    # To make user searchable, need to define how to search User model from Subscription
    # This might require more advanced setup for search if 'user.email' doesn't work directly.

# You can create custom views for other models as well, inheriting from AdminModelView
# e.g., CountryModelView, LawModelView, etc.

def init_admin(app, db_instance, *models_to_register):
    admin_app = Admin(app, name='Consultorio Admin', template_mode='bootstrap4') # Use bootstrap4

    # Add model views
    admin_app.add_view(UserModelView(User, db_instance.session, name='Usuarios'))

    # Register other models passed to the function
    for model_cls, model_name in models_to_register:
        if model_cls == User: # Already added with custom view
            continue
        if model_cls == Subscription:
            admin_app.add_view(SubscriptionModelView(model_cls, db_instance.session, name=model_name))
        else:
            # For other models, use the base AdminModelView or create specific ones if needed
            admin_app.add_view(AdminModelView(model_cls, db_instance.session, name=model_name))

    return admin_app
