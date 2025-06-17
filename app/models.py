from datetime import datetime
from app import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    nombre = db.Column(db.String(100))
    idioma_preferido = db.Column(db.String(10), default='es') # e.g., 'es', 'en'
    pais_interes = db.Column(db.String(50), default='Ecuador') # Storing full name 'Ecuador' as per instructions for now
    tipo_suscripcion = db.Column(db.String(50), default='free') # e.g., 'free', 'premium_monthly', 'premium_annual'
    email_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    # Relationships
    subscriptions = db.relationship('Subscription', backref='subscriber', lazy='dynamic', order_by='desc(Subscription.start_date)')
    lawyer_profile = db.relationship('LawyerProfile', backref='user', uselist=False) # One-to-one
    articles_authored = db.relationship('Article', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_active_premium_subscription(self):
        from datetime import datetime # Ensure datetime is imported
        active_premium_sub = Subscription.query.filter_by(
            user_id=self.id,
            subscription_type='premium',
            status='active'
        ).order_by(Subscription.start_date.desc()).first() # Get the most recent active premium subscription

        if active_premium_sub:
            if active_premium_sub.end_date is None: # For perpetual subscriptions (not used here but good practice)
                return True
            return active_premium_sub.end_date >= datetime.utcnow()
        return False

    @property
    def is_authenticated(self):
        # In a real Flask-Login setup, this would be more robust.
        # For Flask-Admin basic check, this indicates the user object is valid.
        return True

    def __repr__(self):
        return f'<User {self.email}>'

class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    code = db.Column(db.String(2), nullable=False, unique=True) # ISO 3166-1 alpha-2

    laws = db.relationship('Law', backref='country', lazy='dynamic')
    legal_terms = db.relationship('LegalTerm', backref='country', lazy='dynamic')
    articles = db.relationship('Article', backref='country', lazy='dynamic')
    events = db.relationship('Event', backref='country', lazy='dynamic')
    lawyer_profiles = db.relationship('LawyerProfile', backref='country', lazy='dynamic')

    def __repr__(self):
        return f'<Country {self.name}>'

class Law(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content_summary = db.Column(db.Text)
    full_content_path = db.Column(db.String(255)) # Path to a file or URL
    category = db.Column(db.String(100))
    published_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Law {self.title}>'

class LegalTerm(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)
    term = db.Column(db.String(150), nullable=False)
    definition = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f'<LegalTerm {self.term}>'

class Article(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content_preview = db.Column(db.Text)
    full_content_path = db.Column(db.String(255)) # Path to a file or URL
    author_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Can be nullable if articles can be system-generated
    published_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Article {self.title}>'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200))
    is_premium_content = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Event {self.title}>'

class LawyerProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True) # One-to-one with User
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)
    specialization = db.Column(db.String(150))
    bio = db.Column(db.Text)
    contact_info = db.Column(db.String(200)) # Could be an email, phone, or link to a contact form
    is_premium_profile = db.Column(db.Boolean, default=False)
    # Premium fields for LawyerProfile
    full_bio = db.Column(db.Text)
    direct_phone = db.Column(db.String(50))


    def __repr__(self):
        return f'<LawyerProfile for User {self.user_id}>'

class UserFavoriteLaw(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    law_id = db.Column(db.Integer, db.ForeignKey('law.id'), nullable=False)

    user = db.relationship('User', backref=db.backref('favorite_laws_association', lazy='dynamic'))
    law = db.relationship('Law', backref=db.backref('favored_by_users_association', lazy='dynamic'))

    __table_args__ = (db.UniqueConstraint('user_id', 'law_id', name='_user_law_uc'),)

    def __repr__(self):
        return f'<UserFavoriteLaw User {self.user_id} Law {self.law_id}>'

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subscription_type = db.Column(db.String(50), nullable=False, default='free') # Renamed from 'type'
    start_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_date = db.Column(db.DateTime, nullable=True) # Nullable for ongoing or free subscriptions that don't expire
    status = db.Column(db.String(20), default='active', nullable=False) # e.g., 'active', 'cancelled', 'expired'

    def __repr__(self):
        return f'<Subscription {self.subscription_type} for User {self.user_id}>'
