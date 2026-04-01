"""
iRacing Setup Manager
Multi-user setup catalog, comparison, and recommendation tool.
"""
import os
import logging
from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(level=logging.INFO)

from flask import Flask, render_template, redirect, url_for, request, make_response
from flask_login import LoginManager, current_user, login_user
from config import SECRET_KEY, DATABASE_URL, UPLOAD_FOLDER
from db import db

LOCAL_MODE = os.environ.get('LOCAL_MODE') == '1'
LOCAL_USER_EMAIL = 'local@iracing-setups.local'

app = Flask(
    __name__,
    template_folder=os.environ.get('FLASK_TEMPLATE_FOLDER', 'templates'),
    static_folder=os.environ.get('FLASK_STATIC_FOLDER', 'static'),
)
app.secret_key = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db.init_app(app)

import json as _json
app.jinja_env.filters['fromjson'] = _json.loads

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login_page'

@login_manager.user_loader
def load_user(user_id):
    from models import User
    return db.session.get(User, int(user_id))

from routes.auth      import bp as auth_bp
from routes.dashboard import bp as dashboard_bp
from routes.setups    import bp as setups_bp
from routes.compare   import bp as compare_bp
from routes.recommend import bp as recommend_bp
from routes.download  import bp as download_bp
from routes.scan      import bp as scan_bp

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(setups_bp)
app.register_blueprint(compare_bp)
app.register_blueprint(recommend_bp)
app.register_blueprint(download_bp)
app.register_blueprint(scan_bp)

# Create DB tables and upload folder on first run
with app.app_context():
    db.create_all()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    if LOCAL_MODE:
        # Ensure the local user exists
        from models import User
        if not User.query.filter_by(email=LOCAL_USER_EMAIL).first():
            import secrets as _s
            u = User(email=LOCAL_USER_EMAIL, display_name='Local User')
            u.set_password(_s.token_hex(32))
            db.session.add(u)
            db.session.commit()


if LOCAL_MODE:
    @app.before_request
    def auto_login():
        """In local mode, silently log in as the local user on every request."""
        skip = (
            request.path.startswith('/static') or
            current_user.is_authenticated
        )
        if skip:
            return
        from models import User
        user = User.query.filter_by(email=LOCAL_USER_EMAIL).first()
        if user:
            login_user(user, remember=True)


@app.get('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    return render_template('landing.html')


@app.after_request
def allow_advisor_cors(response):
    """Allow the Setup Advisor (localhost:7701) to POST to /api/* endpoints."""
    origin = request.headers.get('Origin', '')
    if origin.startswith('http://localhost:'):
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    return response

@app.route('/api/advisor-notes', methods=['OPTIONS'])
def advisor_notes_preflight():
    resp = make_response('', 204)
    resp.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
    resp.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    return resp

@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5057))
    app.run(host='0.0.0.0', port=port, debug=False)
