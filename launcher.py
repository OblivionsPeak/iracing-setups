"""
iRacing Setup Manager — Desktop Launcher
Double-click to start the app. Opens in your default browser automatically.
"""
import sys
import os
import json
import threading
import webbrowser
import time
import secrets

# When frozen by PyInstaller, resolve paths relative to the exe
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Store data next to the exe so it persists across updates
DATA_DIR = os.path.join(BASE_DIR, 'iracing_data')
os.makedirs(DATA_DIR, exist_ok=True)

# Load or generate a persistent secret key
CONFIG_FILE = os.path.join(DATA_DIR, 'config.json')
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE) as f:
        _cfg = json.load(f)
    _secret_key = _cfg.get('secret_key') or secrets.token_hex(32)
else:
    _secret_key = secrets.token_hex(32)
with open(CONFIG_FILE, 'w') as f:
    json.dump({'secret_key': _secret_key}, f)

# Set env vars before importing app
os.environ['FLASK_SECRET_KEY'] = _secret_key
os.environ['LOCAL_MODE'] = '1'   # single-user exe — skip login entirely
os.environ.setdefault('DATABASE_URL', f"sqlite:///{os.path.join(DATA_DIR, 'iracing_setups.db')}")
os.environ.setdefault('UPLOAD_FOLDER', os.path.join(DATA_DIR, 'setups'))

# Tell Flask/Jinja where to find templates and static files when frozen
if getattr(sys, 'frozen', False):
    os.environ['FLASK_TEMPLATE_FOLDER'] = os.path.join(sys._MEIPASS, 'templates')
    os.environ['FLASK_STATIC_FOLDER'] = os.path.join(sys._MEIPASS, 'static')

PORT = 5057
URL = f"http://localhost:{PORT}"


def open_browser():
    """Wait for the server to start, then open the browser."""
    time.sleep(1.5)
    webbrowser.open(URL)


if __name__ == '__main__':
    print(f"Starting iRacing Setup Manager at {URL}")
    print(f"Data stored in: {DATA_DIR}")
    print("Close this window to stop the app.\n")

    threading.Thread(target=open_browser, daemon=True).start()

    # Import here so env vars are set first
    from app import app
    app.run(host='127.0.0.1', port=PORT, debug=False, use_reloader=False)
