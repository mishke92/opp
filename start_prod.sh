#!/bin/bash

echo "Starting production server..."

# Set environment variables if they are not already set by the environment/platform
# It's generally better to set these in the server environment itself (e.g., systemd unit, Dockerfile, PaaS config).
# This script provides a fallback or an example.

# Ensure FLASK_CONFIG is set to production
export FLASK_CONFIG=${FLASK_CONFIG:-production}
export FLASK_APP=${FLASK_APP:-wsgi.py} # wsgi:app will refer to wsgi.py and the 'app' instance within it

# It's crucial that SECRET_KEY and DATABASE_URL are set in the environment for production.
# The application will fail to start via ProductionConfig if they are not.
# Example check (optional, as Python config should handle this):
# if [ -z "$SECRET_KEY" ] || [ -z "$DATABASE_URL" ]; then
#   echo "ERROR: SECRET_KEY and DATABASE_URL must be set in the environment."
#   exit 1
# fi

# Apply database migrations before starting the app server.
# This is a common practice but ensure your deployment strategy handles this safely
# (e.g., only one instance runs migrations in a multi-instance setup).
echo "Applying database migrations..."
flask db upgrade
if [ $? -ne 0 ]; then
  echo "Database migrations failed. Exiting."
  exit 1
fi
echo "Database migrations applied successfully."

# Start Gunicorn server
# For a Unix socket (often used with Nginx):
# exec gunicorn --workers 3 --bind unix:app.sock -m 007 wsgi:app

# For binding to a TCP port (simpler for direct exposure or some PaaS):
# Use PORT environment variable if provided by the platform (e.g. Heroku, Cloud Run), default to 8000.
APP_PORT=${PORT:-8000}
echo "Starting Gunicorn on port $APP_PORT..."
exec gunicorn --workers ${GUNICORN_WORKERS:-3} --bind 0.0.0.0:${APP_PORT} wsgi:app

# Example with more options:
# exec gunicorn \
#     --workers ${GUNICORN_WORKERS:-3} \
#     --bind 0.0.0.0:${APP_PORT} \
#     --log-level ${GUNICORN_LOG_LEVEL:-info} \
#     --access-logfile '-' \ # Log to stdout
#     --error-logfile '-' \  # Log to stderr
#     wsgi:app

echo "Gunicorn started."
