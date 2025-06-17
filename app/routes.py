from flask import render_template, redirect, url_for, flash, request, session, jsonify
from app import db
from app.models import User, LawyerProfile, Law, LegalTerm, Article, Event, Country, UserFavoriteLaw, Subscription
from urllib.parse import urlparse
from sqlalchemy import or_
from datetime import datetime, timedelta # Added timedelta

# It's better to use Blueprints for organizing routes, especially for auth.
# For now, let's add them directly and then we can refactor to use Blueprints.

# app = create_app() # This would cause issues if we are not in app context

# We need an app context for current_app, or get the app instance differently.
# For simplicity now, let's assume these routes will be registered within create_app
# or we will create a blueprint.

# For now, these routes won't be directly runnable without being registered to an app instance.
# We will create a simple main.py or run.py at the root to run the app later.

def register_routes(app):

    @app.context_processor
    def inject_global_template_variables():
        available_countries = Country.query.order_by(Country.name).all()
        selected_country_code = session.get('selected_country_code', 'EC') # Default to Ecuador

        selected_country_obj = Country.query.filter_by(code=selected_country_code).first()
        if not selected_country_obj and selected_country_code != 'EC': # If invalid code in session, try EC
            selected_country_obj = Country.query.filter_by(code='EC').first()
            if selected_country_obj:
                session['selected_country_code'] = 'EC' # Correct session

        # If still no country (e.g. DB empty, EC not seeded), provide a fallback default
        if not selected_country_obj:
            default_country_display_name = "No configurado"
        else:
            default_country_display_name = selected_country_obj.name

        return dict(
            available_countries=available_countries,
            selected_country_code=session.get('selected_country_code', 'EC'), # Re-get from session after potential correction
            selected_country_object=selected_country_obj,
            default_country_display_name=default_country_display_name # Fallback name for display
        )

    @app.route('/set_country/<country_code>')
    def set_country(country_code):
        country = Country.query.filter_by(code=country_code.upper()).first()
        if country:
            session['selected_country_code'] = country.code.upper()
            flash(f'País cambiado a {country.name}.', 'success')
        else:
            flash(f'No se pudo cambiar al país con código {country_code}.', 'warning')

        # Try to redirect to referrer, fallback to index
        referrer = request.referrer
        if referrer:
            return redirect(referrer)
        return redirect(url_for('index'))


    @app.route('/')
    @app.route('/index')
    def index():
        return render_template('index.html', title='Bienvenido')

    @app.route('/privacy_policy')
    def privacy_policy():
        return render_template('privacy_policy.html', title='Política de Privacidad')

    @app.route('/terms_of_service')
    def terms_of_service():
        return render_template('terms_of_service.html', title='Términos de Servicio')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            nombre = request.form.get('nombre')
            idioma_preferido = request.form.get('idioma_preferido')
            pais_interes = request.form.get('pais_interes')
            accept_privacy = request.form.get('accept_privacy') == 'true'
            accept_terms = request.form.get('accept_terms') == 'true'

            if not email or not password or not nombre:
                flash('Por favor, complete todos los campos obligatorios.', 'danger')
                return render_template('register.html', title='Registrarse')

            if not accept_privacy or not accept_terms:
                flash('Debe aceptar la Política de Privacidad y los Términos de Servicio para registrarse.', 'danger')
                return render_template('register.html', title='Registrarse')

            if User.query.filter_by(email=email).first():
                flash('La dirección de correo electrónico ya está registrada.', 'warning')
                return render_template('register.html', title='Registrarse')

            user = User(
                email=email,
                nombre=nombre,
                idioma_preferido=idioma_preferido,
                pais_interes=pais_interes
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('¡Felicidades, ahora eres un usuario registrado!', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', title='Registrarse')

    @app.route('/abogados') # Default for Ecuador
    @app.route('/abogados/<country_code>')
    def abogados(country_code=None):
        selected_country_code = country_code or request.args.get('country', 'EC')
        selected_country = Country.query.filter_by(code=selected_country_code.upper()).first()
        lawyers_list = []
        current_country_name = "Desconocido"

        if not selected_country:
            flash(f'País con código {selected_country_code} no encontrado.', 'warning')
            ecuador_fallback = Country.query.filter_by(code='EC').first()
            if not ecuador_fallback:
                flash('País Ecuador (fallback) no encontrado. No se pueden cargar abogados.', 'danger')
            else:
                selected_country = ecuador_fallback
                flash('Mostrando abogados para Ecuador (país por defecto).', 'info')

        if selected_country:
            current_country_name = selected_country.name
            user_id = session.get('user_id')
            user = db.session.get(User, user_id) if user_id else None # Changed
            is_premium_user = user.has_active_premium_subscription() if user else False

            if is_premium_user:
                lawyers_list = LawyerProfile.query.filter_by(country_id=selected_country.id).all()
            else:
                lawyers_list = LawyerProfile.query.filter_by(country_id=selected_country.id, is_premium_profile=False).all()

        return render_template('lawyers.html', title=f'Abogados en {current_country_name}', lawyers=lawyers_list, is_premium_user=is_premium_user, current_country_name=current_country_name)

    @app.route('/leyes') # Default for Ecuador
    @app.route('/leyes/<country_code>')
    def leyes(country_code=None):
        selected_country_code = country_code or request.args.get('country', 'EC') # Default to EC

        selected_country = Country.query.filter_by(code=selected_country_code.upper()).first()

        if not selected_country:
            flash(f'País con código {selected_country_code} no encontrado.', 'warning')
            # Fallback to Ecuador or show an error/empty page
            ecuador_fallback = Country.query.filter_by(code='EC').first()
            if not ecuador_fallback:
                 flash('País Ecuador (fallback) no encontrado. No se pueden cargar leyes.', 'danger')
                 return render_template('laws.html', title='Leyes', laws_list=[], categories=[], current_country_name="Desconocido")
            selected_country = ecuador_fallback
            flash(f'Mostrando leyes para Ecuador (país por defecto).', 'info')


        user = None
        is_premium_user = False
        user_id = session.get('user_id')
        if user_id:
            user = db.session.get(User, user_id) # Changed
            if user:
                is_premium_user = user.has_active_premium_subscription()

        query = Law.query.filter_by(country_id=selected_country.id)

        search_term = request.args.get('search')
        category_filter = request.args.get('category')

        if is_premium_user: # Only premium users can search and filter
            if search_term:
                query = query.filter(or_(Law.title.ilike(f'%{search_term}%'), Law.full_content_path.ilike(f'%{search_term}%')))
            if category_filter:
                query = query.filter(Law.category.ilike(f'%{category_filter}%'))

        leyes_list = query.order_by(Law.published_date.desc()).all()

        # Get unique categories for the filter dropdown (only for premium)
        categories = []
        if is_premium_user:
            categories = db.session.query(Law.category).filter(Law.country_id==selected_country.id).distinct().all()
            categories = [c[0] for c in categories if c[0]] # Flatten list and remove None

        favorite_law_ids = []
        if user: # For any logged-in user, check favorites for display state
            favorite_law_ids = [fav.law_id for fav in UserFavoriteLaw.query.filter_by(user_id=user.id).all()]

        return render_template('laws.html', title=f'Leyes de {selected_country.name}', laws_list=leyes_list,
                               current_country_name=selected_country.name,
                               is_premium_user=is_premium_user, categories=categories,
                               search_term=search_term, category_filter=category_filter,
                               favorite_law_ids=favorite_law_ids)

    @app.route('/leyes/<int:law_id>/toggle_favorite', methods=['POST'])
    def toggle_favorite_law(law_id):
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': 'Debes iniciar sesión.'}), 401

        user = db.session.get(User, user_id) # Changed
        if not user or not user.has_active_premium_subscription():
            return jsonify({'success': False, 'message': 'Solo usuarios premium pueden marcar favoritos.'}), 403

        law = db.session.get(Law, law_id) # Changed
        if not law: # Replaced get_or_404 with manual check
            return jsonify({'success': False, 'message': 'Ley no encontrada.'}), 404
        existing_favorite = UserFavoriteLaw.query.filter_by(user_id=user.id, law_id=law.id).first()

        if existing_favorite:
            db.session.delete(existing_favorite)
            db.session.commit()
            return jsonify({'success': True, 'favorited': False, 'message': 'Eliminada de favoritos.'})
        else:
            new_favorite = UserFavoriteLaw(user_id=user.id, law_id=law.id)
            db.session.add(new_favorite)
            db.session.commit()
            return jsonify({'success': True, 'favorited': True, 'message': 'Agregada a favoritos.'})

    @app.route('/mis_leyes_favoritas')
    def mis_leyes_favoritas():
        user_id = session.get('user_id')
        if not user_id:
            flash('Debes iniciar sesión para ver tus leyes favoritas.', 'warning')
            return redirect(url_for('login'))

        user = db.session.get(User, user_id) # Changed
        if not user or not user.has_active_premium_subscription():
            flash('Esta función es solo para usuarios premium.', 'warning')
            return redirect(url_for('leyes')) # Or some other appropriate page

        # Get laws favorited by the user
        favorite_associations = UserFavoriteLaw.query.filter_by(user_id=user.id).all()
        leyes_favoritas_ids = [fav.law_id for fav in favorite_associations]
        leyes_list = Law.query.filter(Law.id.in_(leyes_favoritas_ids)).all()

        return render_template('favorite_laws.html', title='Mis Leyes Favoritas', laws_list=leyes_list)


    @app.route('/terminologia') # Default for Ecuador
    @app.route('/terminologia/<country_code>')
    def terminologia(country_code=None):
        selected_country_code = country_code or request.args.get('country', 'EC')
        selected_country = Country.query.filter_by(code=selected_country_code.upper()).first()
        terms_list = []
        current_country_name = "Desconocido"

        if not selected_country:
            flash(f'País con código {selected_country_code} no encontrado.', 'warning')
            ecuador_fallback = Country.query.filter_by(code='EC').first()
            if not ecuador_fallback:
                flash('País Ecuador (fallback) no encontrado. No se pueden cargar términos.', 'danger')
            else:
                selected_country = ecuador_fallback
                flash('Mostrando terminología para Ecuador (país por defecto).', 'info')

        if selected_country:
            current_country_name = selected_country.name
            user_id = session.get('user_id')
            user = db.session.get(User, user_id) if user_id else None # Changed
            is_premium_user = user.has_active_premium_subscription() if user else False

            if is_premium_user:
                terms_list = LegalTerm.query.filter_by(country_id=selected_country.id).all()
            else:
                terms_list = LegalTerm.query.filter_by(country_id=selected_country.id).limit(5).all() # Show first 5 for free tier

        return render_template('legal_terms.html', title=f'Terminología Legal de {current_country_name}', terms=terms_list, is_premium_user=is_premium_user, current_country_name=current_country_name)

    @app.route('/noticias') # Default for Ecuador
    @app.route('/noticias/<country_code>')
    def noticias(country_code=None):
        selected_country_code = country_code or request.args.get('country', 'EC')
        selected_country = Country.query.filter_by(code=selected_country_code.upper()).first()
        articles_list = []
        current_country_name = "Desconocido"

        if not selected_country:
            flash(f'País con código {selected_country_code} no encontrado.', 'warning')
            ecuador_fallback = Country.query.filter_by(code='EC').first()
            if not ecuador_fallback:
                flash('País Ecuador (fallback) no encontrado. No se pueden cargar noticias.', 'danger')
            else:
                selected_country = ecuador_fallback
                flash('Mostrando noticias para Ecuador (país por defecto).', 'info')

        if selected_country:
            current_country_name = selected_country.name
            articles_list = Article.query.filter_by(country_id=selected_country.id).order_by(Article.published_date.desc()).all()

        user_id = session.get('user_id')
        is_premium_user = False
        if user_id:
            user = db.session.get(User, user_id) # Changed
            if user:
                is_premium_user = user.has_active_premium_subscription()

        return render_template('articles.html', title=f'Noticias y Blog de {current_country_name}', articles_list=articles_list, is_premium_user=is_premium_user, current_country_name=current_country_name)

    @app.route('/eventos') # Default for Ecuador
    @app.route('/eventos/<country_code>')
    def eventos(country_code=None):
        selected_country_code = country_code or request.args.get('country', 'EC')
        selected_country = Country.query.filter_by(code=selected_country_code.upper()).first()
        events_list = []
        current_country_name = "Desconocido"

        if not selected_country:
            flash(f'País con código {selected_country_code} no encontrado.', 'warning')
            ecuador_fallback = Country.query.filter_by(code='EC').first()
            if not ecuador_fallback:
                flash('País Ecuador (fallback) no encontrado. No se pueden cargar eventos.', 'danger')
            else:
                selected_country = ecuador_fallback
                flash('Mostrando eventos para Ecuador (país por defecto).', 'info')

        if selected_country:
            current_country_name = selected_country.name
            user_id = session.get('user_id')
            user = db.session.get(User, user_id) if user_id else None # Changed
            is_premium_user = user.has_active_premium_subscription() if user else False

            if is_premium_user:
                events_list = Event.query.filter_by(country_id=selected_country.id).order_by(Event.event_date.asc()).all()
            else:
                events_list = Event.query.filter_by(country_id=selected_country.id, is_premium_content=False).order_by(Event.event_date.asc()).all()

        return render_template('events.html', title=f'Eventos en {current_country_name}', events_list=events_list, is_premium_user=is_premium_user, current_country_name=current_country_name)

    @app.route('/contacto')
    def contacto():
        return render_template('contact.html', title='Contacto')

    @app.route('/chatbot')
    def chatbot():
        user_id = session.get('user_id')
        is_premium_user = False
        if user_id:
            user = db.session.get(User, user_id) # Changed
            if user:
            user = db.session.get(User, user_id) # Changed
            if user:
                is_premium_user = user.has_active_premium_subscription()
        return render_template('chatbot.html', title='Chatbot', is_premium_user=is_premium_user)

    @app.route('/agendar_cita')
    def agendar_cita():
        user_id = session.get('user_id')
        is_premium_user = False
        if user_id:
            user = User.query.get(user_id)
            if user: # Check if user exists
                is_premium_user = user.has_active_premium_subscription()
        return render_template('schedule_appointment.html', title='Agendar Cita', is_premium_user=is_premium_user)

    @app.route('/mis_casos')
    def my_cases():
        if 'user_id' not in session:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login', next=url_for('my_cases')))

        # Further logic can be added here to fetch actual cases for the user
        # For now, just rendering the template
        user = db.session.get(User, session['user_id']) # Changed
        is_premium_user = user.has_active_premium_subscription() if user else False
        return render_template('my_cases.html', title='Mis Casos', is_premium_user=is_premium_user)

    @app.route('/generar_documento')
    def document_generator():
        user_id = session.get('user_id')
        if not user_id:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('login', next=url_for('document_generator')))

        user = db.session.get(User, user_id) # Changed
        is_premium_user = user.has_active_premium_subscription() if user else False

        if not is_premium_user:
            # Render the same template, but it will show the "Upgrade to Premium" message
            flash('El generador de documentos es una función Premium.', 'warning')
            # return redirect(url_for('index')) # Or a specific "upgrade" page

        # For now, just rendering the template, which handles display based on is_premium_user
        return render_template('document_generator.html', title='Generador de Documentos', is_premium_user=is_premium_user)

    @app.route('/planes')
    def subscription_plans():
        user_id = session.get('user_id')
        current_user = db.session.get(User, user_id) if user_id else None # Changed
        # Pass current_user to check has_active_premium_subscription in template
        return render_template('subscription_plans.html', title='Planes de Suscripción', current_user=current_user)

    @app.route('/subscribe/premium', methods=['POST'])
    def subscribe_premium():
        user_id = session.get('user_id')
        if not user_id:
            flash('Debes iniciar sesión para suscribirte.', 'warning')
            return redirect(url_for('login', next=url_for('subscription_plans')))

        current_user = db.session.get(User, user_id) # Changed
        if not current_user:
            flash('Usuario no encontrado.', 'danger')
            return redirect(url_for('subscription_plans'))

        if current_user.has_active_premium_subscription():
            flash('Ya tienes una suscripción Premium activa.', 'info')
            return redirect(url_for('my_profile')) # Or subscription_plans

        # Deactivate any existing 'active' or 'expired' subscriptions for the user to avoid multiple active ones
        existing_subscriptions = Subscription.query.filter_by(user_id=current_user.id).all()
        for sub in existing_subscriptions:
            if sub.status == 'active':
                sub.status = 'cancelled' # Or 'expired' if it makes more sense
                sub.end_date = datetime.utcnow() - timedelta(seconds=1) # Expire immediately

        # Create new premium subscription
        new_subscription = Subscription(
            user_id=current_user.id,
            subscription_type='premium',
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30),
            status='active'
        )
        db.session.add(new_subscription)

        # Update user's convenience field
        current_user.tipo_suscripcion = 'premium'
        db.session.add(current_user)

        db.session.commit()

        flash('¡Felicidades! Ahora tienes una suscripción Premium activa por 30 días.', 'success')
        return redirect(url_for('my_profile'))

    @app.route('/mi_perfil')
    def my_profile():
        user_id = session.get('user_id')
        if not user_id:
            flash('Debes iniciar sesión para ver tu perfil.', 'warning')
            return redirect(url_for('login', next=url_for('my_profile')))

        current_user = db.session.get(User, user_id) # Changed
        if not current_user:
            flash('Usuario no encontrado.', 'danger')
            session.pop('user_id', None) # Clear invalid session
            return redirect(url_for('login'))

        # For displaying end_date correctly in template
        from datetime import datetime as dt_for_template

        return render_template('my_profile.html', title='Mi Perfil', current_user=current_user, today_date=dt_for_template.utcnow())

    @app.route('/cancel_subscription', methods=['POST'])
    def cancel_subscription():
        user_id = session.get('user_id')
        if not user_id:
            flash('Debes iniciar sesión para cancelar una suscripción.', 'warning')
            return redirect(url_for('login'))

        current_user = db.session.get(User, user_id) # Changed
        if not current_user:
            flash('Usuario no encontrado.', 'danger')
            return redirect(url_for('login'))

        active_premium_sub = Subscription.query.filter(
            Subscription.user_id == current_user.id,
            Subscription.subscription_type == 'premium',
            Subscription.status == 'active',
            # Subscription.end_date >= datetime.utcnow() # Ensure it's truly active now
        ).order_by(Subscription.start_date.desc()).first()

        if active_premium_sub:
            # Instead of immediate cancellation, usually you'd set it to cancel at period end.
            # For this simulation, we'll change status and update user.tipo_suscripcion.
            # A real system might keep premium status until end_date.
            active_premium_sub.status = 'cancelled'
            # active_premium_sub.end_date = datetime.utcnow() # Or keep original end_date

            # If User.tipo_suscripcion should reflect immediate loss of premium features:
            current_user.tipo_suscripcion = 'free'
            db.session.add(current_user)
            db.session.add(active_premium_sub)
            db.session.commit()
            flash('Tu suscripción Premium ha sido marcada para cancelación. Seguirás teniendo acceso Premium hasta la fecha de finalización si aplica, o el acceso se ha revocado inmediatamente según la configuración del sistema.', 'info')
        else:
            flash('No se encontró una suscripción Premium activa para cancelar.', 'warning')

        return redirect(url_for('my_profile'))


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            remember_me = request.form.get('remember_me') is not None

            user = User.query.filter_by(email=email).first()

            if user is None or not user.check_password(password):
                flash('Invalid email or password.', 'danger')
                return render_template('login.html', title='Sign In')

            # Using Flask session for login status
            session['user_id'] = user.id
            flash(f'Welcome back, {user.nombre}!', 'success')

            # TODO: Implement proper "next" page redirection
            # next_page = request.args.get('next')
            # if not next_page or url_parse(next_page).netloc != '':
            #     next_page = url_for('index')
            return redirect(url_for('index'))
        return render_template('login.html', title='Sign In')

    @app.route('/logout')
    def logout():
        session.pop('user_id', None)
        flash('You have been logged out.', 'info')
        return redirect(url_for('index'))

    @app.route('/guest_login')
    def guest_login():
        session['guest_mode'] = True
        session.pop('user_id', None) # Ensure no user is logged in
        flash('You are now browsing as a guest.', 'info')
        return redirect(url_for('index'))

    # Example of a protected route
    @app.route('/profile')
    def profile():
        if 'user_id' not in session and 'guest_mode' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))

        if 'guest_mode' in session:
            user_info = "Guest User"
        else:
            user = db.session.get(User, session['user_id']) # Changed
            user_info = user.nombre if user else "Unknown User"

        return f"This is your profile page, {user_info}."

# The routes need to be registered with the Flask app instance.
# This will be done in __init__.py or by using Blueprints.
# For now, modifying __init__.py to call register_routes.
# from app import create_app
# app = create_app()
# register_routes(app)

# To make this file self-contained for now for linting, let's define a dummy app
# if __name__ == '__main__':
#     from flask import Flask
#     app_dummy = Flask(__name__)
#     # Minimal config for session
#     app_dummy.config['SECRET_KEY'] = 'dummy_secret_key_for_testing_routes'
#     # db.init_app(app_dummy) # This would require full app context
#     # register_routes(app_dummy)
#     # app_dummy.run(debug=True)
