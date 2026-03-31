"""Dashboard home."""
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Setup
from data.cars import car_display_name, car_class, CLASS_ORDER
from data.tracks import track_display_name

bp = Blueprint('dashboard', __name__)


@bp.get('/dashboard')
@login_required
def home():
    setups = Setup.query.filter_by(user_id=current_user.id) \
        .order_by(Setup.uploaded_at.desc()).all()

    total      = len(setups)
    cars_set   = {s.car_key for s in setups}
    tracks_set = {s.track_key for s in setups}

    # Car counts grouped by class
    car_counts = {}
    for s in setups:
        car_counts[s.car_key] = car_counts.get(s.car_key, 0) + 1

    cars_by_class = {}
    for key, count in sorted(car_counts.items()):
        cls = car_class(key)
        cars_by_class.setdefault(cls, [])
        cars_by_class[cls].append({
            'key':   key,
            'name':  car_display_name(key),
            'count': count,
        })
    cars_display = [(cls, cars_by_class[cls]) for cls in CLASS_ORDER if cls in cars_by_class]

    recent = [{
        'id':           s.id,
        'car_display':  s.car_name or car_display_name(s.car_key),
        'track_display': s.track_name or track_display_name(s.track_key),
        'setup_type':   s.setup_type,
    } for s in setups[:5]]

    return render_template(
        'dashboard.html',
        total=total,
        cars_count=len(cars_set),
        tracks_count=len(tracks_set),
        cars_display=cars_display,
        recent=recent,
    )
