import os

SUPABASE_URL      = os.environ['SUPABASE_URL']
SUPABASE_ANON_KEY = os.environ['SUPABASE_ANON_KEY']
SUPABASE_SVC_KEY  = os.environ['SUPABASE_SERVICE_KEY']
SECRET_KEY        = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-me')
APP_URL           = os.environ.get('APP_URL', '')
