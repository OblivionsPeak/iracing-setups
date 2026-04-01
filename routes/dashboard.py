"""Dashboard home."""
from datetime import date, datetime, timezone
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Setup
from data.cars import car_display_name, car_class, CLASS_ORDER
from data.tracks import track_display_name

bp = Blueprint('dashboard', __name__)

# Approximate iRacing season start dates (Tuesday of week 1)
_SEASON_STARTS = [
    (2025, 1, date(2025, 1,  7)),
    (2025, 2, date(2025, 4,  8)),
    (2025, 3, date(2025, 7,  8)),
    (2025, 4, date(2025, 10, 7)),
    (2026, 1, date(2026, 1,  6)),
    (2026, 2, date(2026, 4,  7)),
    (2026, 3, date(2026, 7,  7)),
    (2026, 4, date(2026, 10, 6)),
    (2027, 1, date(2027, 1,  5)),
]


def _current_season():
    today = date.today()
    current = None
    for i, (yr, sn, start) in enumerate(_SEASON_STARTS):
        if start <= today:
            # Find end: next season start or +12 weeks
            if i + 1 < len(_SEASON_STARTS):
                end = _SEASON_STARTS[i + 1][2]
            else:
                from datetime import timedelta
                end = start + timedelta(weeks=12)
            week = min(12, (today - start).days // 7 + 1)
            current = {
                'year':       yr,
                'season':     sn,
                'week':       week,
                'start':      start,
                'end':        end,
                'label':      f'{yr} S{sn}',
                'next_label': f'{_SEASON_STARTS[i+1][0]} S{_SEASON_STARTS[i+1][1]}' if i+1 < len(_SEASON_STARTS) else None,
                'days_left':  (end - today).days,
            }
    return current


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

    # Recently used: order by last_used_at then uploaded_at
    recently_used = Setup.query.filter_by(user_id=current_user.id) \
        .order_by(Setup.last_used_at.desc().nullslast(), Setup.uploaded_at.desc()) \
        .limit(5).all()

    recent = [{
        'id':           s.id,
        'car_display':  s.car_name or car_display_name(s.car_key),
        'track_display': s.track_name or track_display_name(s.track_key),
        'setup_type':   s.setup_type,
        'rating':       s.rating,
        'last_used_at': s.last_used_at,
    } for s in recently_used]

    # Cars with no setups added this season (coverage gap alert)
    season = _current_season()
    season_gap_cars = []
    if season and setups:
        season_start = datetime(season['start'].year, season['start'].month, season['start'].day, tzinfo=timezone.utc)
        season_uploads = {s.car_key for s in setups if s.uploaded_at and s.uploaded_at.replace(tzinfo=timezone.utc) >= season_start}
        all_user_cars  = {s.car_key for s in setups}
        season_gap_cars = [
            {'key': k, 'name': car_display_name(k)}
            for k in sorted(all_user_cars - season_uploads)
        ][:5]  # cap at 5

    return render_template(
        'dashboard.html',
        total=total,
        cars_count=len(cars_set),
        tracks_count=len(tracks_set),
        cars_display=cars_display,
        recent=recent,
        season=season,
        season_gap_cars=season_gap_cars,
    )
