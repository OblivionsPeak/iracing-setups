"""
iRacing Setup Manager
Multi-user setup catalog, comparison, and recommendation tool.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
from config import SECRET_KEY, DATABASE_URL, UPLOAD_FOLDER
from db import db

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

app.register_blueprint(auth_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(setups_bp)
app.register_blueprint(compare_bp)
app.register_blueprint(recommend_bp)
app.register_blueprint(download_bp)

# Create DB tables and upload folder on first run
with app.app_context():
    db.create_all()
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.get('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    return render_template('landing.html')


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5057))
    app.run(host='0.0.0.0', port=port, debug=False)
