"""Dashboard home and login_required decorator."""
from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, session
from supabase_client import svc_client
from data.cars import car_display_name, car_class, CLASS_ORDER
from data.tracks import track_display_name

bp = Blueprint('dashboard', __name__)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user'):
            return redirect(url_for('auth.login_page'))
        return f(*args, **kwargs)
    return decorated


@bp.get('/dashboard')
@login_required
def home():
    user_id = session['user']['id']

    # Summary counts
    setups_res = svc_client.table('setups').select('id, car_key, car_class, track_key, uploaded_at, last_used_at') \
        .eq('user_id', user_id).order('uploaded_at', desc=True).execute()
    setups = setups_res.data or []

    total      = len(setups)
    cars_set   = set(s['car_key'] for s in setups)
    tracks_set = set(s['track_key'] for s in setups)

    # Cars with setup counts, grouped by class
    car_counts = {}
    for s in setups:
        k = s['car_key']
        car_counts[k] = car_counts.get(k, 0) + 1

    cars_by_class = {}
    for car_key, count in sorted(car_counts.items(), key=lambda x: x[0]):
        cls = car_class(car_key)
        cars_by_class.setdefault(cls, [])
        cars_by_class[cls].append({
            'key':   car_key,
            'name':  car_display_name(car_key),
            'count': count,
        })
    # Ordered by class
    cars_display = [(cls, cars_by_class[cls]) for cls in CLASS_ORDER if cls in cars_by_class]

    # Recent setups (last 5)
    recent = []
    for s in setups[:5]:
        recent.append({
            **s,
            'car_display':   car_display_name(s['car_key']),
            'track_display': track_display_name(s['track_key']),
        })

    return render_template(
        'dashboard.html',
        total=total,
        cars_count=len(cars_set),
        tracks_count=len(tracks_set),
        cars_display=cars_display,
        recent=recent,
    )
