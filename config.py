import os

SECRET_KEY    = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-me')
DATABASE_URL  = os.environ.get('DATABASE_URL', 'sqlite:///iracing_setups.db')
UPLOAD_FOLDER = os.environ.get(
    'UPLOAD_FOLDER',
    os.path.join(os.path.dirname(__file__), 'uploads', 'setups')
)
