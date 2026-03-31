"""Setup recommendation and gap report."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Setup
from data.cars import car_display_name, car_class, all_cars_grouped, CLASS_ORDER
from data.tracks import track_display_name, TRACK_LIST
from data.track_categories import get_category, same_category_tracks

bp = Blueprint('recommend', __name__)


def _find_best(setups, track_key):
    exact = [s for s in setups if s.track_key == track_key]
    if exact:
        exact.sort(key=lambda s: (s.last_used_at or s.uploaded_at), reverse=True)
        return exact[0], 'exact_match'

    cat = get_category(track_key)
    if cat:
        same_cat = [s for s in setups if s.track_key in same_category_tracks(track_key)]
        if same_cat:
            same_cat.sort(key=lambda s: (s.last_used_at or s.uploaded_at), reverse=True)
            return same_cat[0], f'same_category:{cat}'

    if setups:
        best = sorted(setups, key=lambda s: (s.last_used_at or s.uploaded_at), reverse=True)[0]
        return best, 'any_car_setup'

    return None, 'no_setups'


@bp.get('/recommend')
@login_required
def recommend_page():
    return render_template('recommend.html', track_list=TRACK_LIST, cars=all_cars_grouped())


@bp.post('/recommend')
@login_required
def recommend():
    car_key   = request.form.get('car_key', '').strip()
    track_key = request.form.get('track_key', '').strip()

    if not car_key or not track_key:
        flash('Please select both a car and a track.', 'danger')
        return redirect(url_for('recommend.recommend_page'))

    setups = Setup.query.filter_by(user_id=current_user.id, car_key=car_key).all()
    best, reason = _find_best(setups, track_key)

    reason_text = _reason_text(reason, car_key, track_key, best)

    return render_template(
        'recommend_result.html',
        car_display=car_display_name(car_key),
        track_display=track_display_name(track_key),
        best=best,
        reason=reason,
        reason_text=reason_text,
        car_key=car_key,
        track_key=track_key,
    )


def _reason_text(reason, car_key, track_key, best):
    car   = car_display_name(car_key)
    track = track_display_name(track_key)
    if reason == 'exact_match':
        return f'Found a setup for the {car} specifically at {track}.'
    if reason.startswith('same_category:'):
        cat = reason.split(':')[1].replace('_', ' ').title()
        best_track = best.track_name if best else '—'
        return (f'No {track} setup found. Recommending your {best_track} setup — '
                f'both are {cat} circuits with similar characteristics.')
    if reason == 'any_car_setup':
        best_track = best.track_name if best else '—'
        return (f'No {track} setup or similar circuit found. '
                f'Using your {best_track} setup as a starting baseline.')
    return f'No {car} setups in your library yet.'


@bp.get('/gaps')
@login_required
def gap_report():
    setups = Setup.query.filter_by(user_id=current_user.id).all()
    covered = {(s.car_key, s.track_key) for s in setups}

    user_cars = {}
    for s in setups:
        if s.car_key not in user_cars:
            user_cars[s.car_key] = {'name': s.car_name, 'class': s.car_class}

    cars_by_class = {}
    for k, info in user_cars.items():
        cls = info['class']
        cars_by_class.setdefault(cls, [])
        cars_by_class[cls].append({'key': k, 'name': info['name']})
    for cls in cars_by_class:
        cars_by_class[cls].sort(key=lambda x: x['name'])

    ordered_cars = [(cls, cars_by_class[cls]) for cls in CLASS_ORDER if cls in cars_by_class]

    tracks = sorted(
        {(s.track_key, s.track_name) for s in setups},
        key=lambda x: x[1]
    )

    return render_template('gap_report.html', ordered_cars=ordered_cars, tracks=tracks, covered=covered)
