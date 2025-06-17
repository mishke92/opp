import pytest
from flask.testing import FlaskCliRunner

def test_seed_db_command(runner: FlaskCliRunner, app, db):
    # The 'db' fixture ensures the database is clean and tables are created.
    # We are testing if the command runs without error.
    # Verifying exact data seeding can be complex and might be better for specific unit tests
    # or more focused integration tests if specific seeded data is critical for a scenario.

    # Ensure the command is available in the app's cli runner
    assert 'seed-db' in app.cli.commands
    result = runner.invoke(app.cli.commands['seed-db'])

    # print(f"Output: {result.output}") # For debugging if needed
    # print(f"Exception: {result.exception}")
    # print(f"Exit code: {result.exit_code}")

    assert result.exit_code == 0, f"seed-db command failed: {result.output}"
    assert "Database seeded!" in result.output
    assert "Ecuador seeded." in result.output # Check for one of the expected messages
    assert "Users seeded (including admin)." in result.output
    # Add more assertions for other seed functions if desired

    # You could add checks here to see if some basic data was indeed added,
    # e.g., Country.query.count() > 0, User.query.filter_by(is_admin=True).count() > 0
    # This depends on how much overlap you want with model tests or specific data tests.
    from app.models import Country, User
    assert Country.query.count() >= 4 # EC, CO, PE, ES
    assert User.query.filter_by(email='admin@example.com').first() is not None
    assert User.query.filter_by(email='testuser1@example.com').first() is not None

    # Test running it again (should not duplicate data if functions have checks)
    result_rerun = runner.invoke(args=['seed-db'])
    assert result_rerun.exit_code == 0, f"seed-db command re-run failed: {result_rerun.output}"
    assert "already exists" in result_rerun.output # Expect messages about data already existing
    assert "Database seeded!" in result_rerun.output # Final message should still be there
