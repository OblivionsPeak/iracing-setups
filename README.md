# iRacing Setups

A multi-user web app for managing, comparing, and recommending iRacing car setups.
No cloud accounts required — runs on SQLite and the local filesystem.

## Features

- **Upload & Decode** — Upload `.sto` files and instantly see all parameters decoded (aero, suspension, diff, brakes) organized by garage tab and section
- **Browse & Filter** — Filter your library by car class, car, or track
- **Side-by-Side Compare** — Select any two setups and see exactly what differs, with differences highlighted
- **Setup Recommender** — Pick a car and track, get your best matching setup with a reason why
- **Gap Report** — Visual car × track coverage matrix showing which combinations you're missing
- **Download** — Download any `.sto` file to load directly in iRacing
- **Multi-User** — Each driver has their own private library

Supports GT3, GT4, GTE, LMP2, LMP3, GTP, and Porsche Cup cars.

## How It Works

iRacing `.sto` setup files contain an encrypted binary section followed by UTF-16 text notes. The app sends each uploaded file to the [setupdelta.com](https://www.setupdelta.com) decode API, which returns all named setup parameters with values and ranges. The decoded data and original `.sto` file are stored locally.

## Stack

- **Backend:** Python / Flask
- **Database:** SQLite (via SQLAlchemy — zero config, single file)
- **Auth:** Flask-Login + Werkzeug password hashing
- **File Storage:** Local filesystem
- **Decoding:** setupdelta.com API (free, no account needed)
- **Deployment:** Render (or any server with Python)

## Run Locally

```bash
git clone https://github.com/OblivionsPeak/iracing-setups.git
cd iracing-setups

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env            # edit FLASK_SECRET_KEY

python app.py
```

Open [http://localhost:5057](http://localhost:5057). The SQLite database and uploads folder are created automatically on first run.

## Deploy to Render (Free)

1. Push to GitHub
2. Go to [render.com](https://render.com) → New Web Service → connect your repo
3. Render detects `render.yaml` automatically
4. Set one env var: `FLASK_SECRET_KEY` (or let Render generate it)
5. Deploy

The `render.yaml` includes a 1 GB persistent disk at `/data` for the database and uploaded `.sto` files. This costs ~$0.25/month on Render's paid plans. On the free tier, data resets on each deploy — fine for testing, use the paid starter ($7/mo) for a permanent library.

### Alternative: Fly.io (Free persistent storage)

```bash
fly launch   # follow prompts
fly volumes create iracing_data --size 1
fly deploy
```

Set `DATABASE_URL=sqlite:////data/iracing_setups.db` and `UPLOAD_FOLDER=/data/setups` as Fly secrets.

### Alternative: Any VPS

```bash
git clone ... && cd iracing-setups
pip install -r requirements.txt
cp .env.example .env  # fill in values
gunicorn app:app --workers 1 --threads 4 --bind 0.0.0.0:5057
```

## Password Reset

There is no email-based password reset. To reset a password manually:

```python
from app import app, db
from models import User
with app.app_context():
    u = User.query.filter_by(email='user@example.com').first()
    u.set_password('newpassword')
    db.session.commit()
```

## Notes

- The app depends on [setupdelta.com](https://www.setupdelta.com) to decode `.sto` files. If it's unavailable, new uploads fail but existing setups remain accessible.
- iRacing `.sto` binary sections use proprietary encryption. This app reads them via setupdelta — it does not modify the binary.
- Each user's data is isolated by `user_id` filtering in every query.
