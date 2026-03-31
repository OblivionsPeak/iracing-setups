"""
iRacing Setup Manager
Multi-user setup catalog, comparison, and recommendation tool.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, redirect, url_for, session
from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

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


@app.get('/')
def index():
    if session.get('user'):
        return redirect(url_for('dashboard.home'))
    return render_template('landing.html')


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5057))
    app.run(host='0.0.0.0', port=port, debug=False)
