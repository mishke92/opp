from app import create_app, db
from app.models import User, Country, Law, LegalTerm, Article, Event, LawyerProfile, Subscription

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Country': Country,
        'Law': Law,
        'LegalTerm': LegalTerm,
        'Article': Article,
        'Event': Event,
        'LawyerProfile': LawyerProfile,
        'Subscription': Subscription
    }

if __name__ == '__main__':
    app.run(debug=True)


# Custom CLI command to seed data
@app.cli.command("seed-db")
def seed_db_command():
    """Seeds the database with initial data."""
    from seed_data import seed_all
    seed_all()
    print("Database seeded!")
