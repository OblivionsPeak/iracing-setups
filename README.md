# iRacing Setups

A multi-user web app for managing, comparing, and recommending iRacing car setups.

## Features

- **Upload & Decode** — Upload `.sto` files and instantly see all parameters decoded (aero, suspension, diff, brakes) organized by garage tab and section
- **Browse & Filter** — Filter your library by car class, car, or track
- **Side-by-Side Compare** — Select any two setups and see exactly what differs, with differences highlighted
- **Setup Recommender** — Pick a car and track, get your best matching setup from your library with a reason why
- **Gap Report** — Visual car × track coverage matrix showing which combinations you're missing
- **Download** — Download any `.sto` file directly to load in iRacing

Supports GT3, GT4, GTE, LMP2, LMP3, GTP, and Porsche Cup cars.

## How It Works

iRacing `.sto` setup files contain a binary encrypted section followed by a UTF-16 text notes section. The app sends each uploaded file to the [setupdelta.com](https://www.setupdelta.com) API for decoding, which returns all named setup parameters with values and ranges. The decoded data is stored in Supabase and the original `.sto` file is stored in Supabase Storage.

## Stack

- **Backend:** Python / Flask
- **Database & Auth:** Supabase (PostgreSQL + Supabase Auth)
- **File Storage:** Supabase Storage
- **Deployment:** Railway
- **Decoding:** setupdelta.com API

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/iracing-setups.git
cd iracing-setups
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Run `db/schema.sql` in the Supabase SQL editor
3. Create a private Storage bucket named `setups`
4. Copy your project URL, anon key, and service role key

### 3. Environment variables

```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
FLASK_SECRET_KEY=change-me-to-a-random-string
APP_URL=http://localhost:5057
```

### 4. Run locally

```bash
python app.py
```

Open [http://localhost:5057](http://localhost:5057)

## Deploy to Railway

1. Push to GitHub
2. Create a new Railway project, connect your repo
3. Set environment variables in Railway dashboard (same as `.env`)
4. Railway auto-detects the `Procfile` and deploys

## Notes

- The app depends on the [setupdelta.com](https://www.setupdelta.com) API to decode `.sto` files. This is a third-party service — if it's unavailable, new uploads will fail but existing setups remain accessible.
- iRacing `.sto` files use proprietary encryption. We read-only decode them via setupdelta; we do not modify the binary.
- Each user's setups are private. Row-level security is enforced in Supabase.
