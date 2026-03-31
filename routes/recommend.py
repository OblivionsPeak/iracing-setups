"""Setup recommendation and gap report."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from supabase_client import svc_client
from routes.dashboard import login_required
from data.cars import car_display_name, car_class, all_cars_grouped, CARS, CLASS_ORDER
from data.tracks import track_display_name, TRACK_LIST, TRACKS
from data.track_categories import get_category, same_category_tracks

bp = Blueprint('recommend', __name__)


def _find_best_setup(setups: list, track_key: str) -> tuple[dict | None, str]:
    """
    Return (best_setup, reason_string).
    Priority: exact track > same category > any setup for car.
    """
    # 1. Exact match
    exact = [s for s in setups if s['track_key'] == track_key]
    if exact:
        # Prefer most recently used, then most recently uploaded
        exact.sort(key=lambda s: (s.get('last_used_at') or '', s.get('uploaded_at') or ''), reverse=True)
        return exact[0], 'exact_match'

    # 2. Same category
    category = get_category(track_key)
    if category:
        same_cat = [s for s in setups if s['track_key'] in same_category_tracks(track_key)]
        if same_cat:
            same_cat.sort(key=lambda s: (s.get('last_used_at') or '', s.get('uploaded_at') or ''), reverse=True)
            return same_cat[0], f'same_category:{category}'

    # 3. Any setup for this car
    if setups:
        setups_sorted = sorted(setups, key=lambda s: (s.get('last_used_at') or '', s.get('uploaded_at') or ''), reverse=True)
        return setups_sorted[0], 'any_car_setup'

    return None, 'no_setups'


@bp.get('/recommend')
@login_required
def recommend_page():
    return render_template('recommend.html', track_list=TRACK_LIST, cars=all_cars_grouped())


@bp.post('/recommend')
@login_required
def recommend():
    user_id   = session['user']['id']
    car_key   = request.form.get('car_key', '').strip()
    track_key = request.form.get('track_key', '').strip()

    if not car_key or not track_key:
        flash('Please select both a car and a track.', 'danger')
        return redirect(url_for('recommend.recommend_page'))

    # All setups for this car
    res = svc_client.table('setups').select(
        'id, filename, car_key, car_name, track_key, track_name, setup_type, uploaded_at, last_used_at'
    ).eq('user_id', user_id).eq('car_key', car_key).execute()
    setups = res.data or []

    best, reason = _find_best_setup(setups, track_key)

    if best:
        best['car_display']   = best.get('car_name') or car_display_name(best['car_key'])
        best['track_display'] = best.get('track_name') or track_display_name(best['track_key'])

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


def _reason_text(reason: str, car_key: str, track_key: str, best) -> str:
    car   = car_display_name(car_key)
    track = track_display_name(track_key)
    if reason == 'exact_match':
        return f'Found a setup for the {car} specifically at {track}.'
    if reason.startswith('same_category:'):
        cat = reason.split(':')[1].replace('_', ' ').title()
        best_track = track_display_name(best['track_key']) if best else '—'
        return (f'No setup for {track} in your library. Recommending your {best_track} setup '
                f'— both are {cat} circuits with similar characteristics.')
    if reason == 'any_car_setup':
        best_track = track_display_name(best['track_key']) if best else '—'
        return (f'No setup for {track} or a similar circuit. '
                f'Using your {best_track} setup as a baseline — adjust aero and ride heights for {track}.')
    return f'No {car} setups found in your library. Upload one to get started.'


@bp.get('/gaps')
@login_required
def gap_report():
    user_id = session['user']['id']

    res = svc_client.table('setups').select('car_key, car_name, car_class, track_key') \
        .eq('user_id', user_id).execute()
    setups = res.data or []

    # Build coverage set
    covered = set((s['car_key'], s['track_key']) for s in setups)

    # Cars user has at least one setup for
    user_cars = {}
    for s in setups:
        k = s['car_key']
        if k not in user_cars:
            user_cars[k] = {
                'name':  s.get('car_name') or car_display_name(k),
                'class': s.get('car_class') or car_class(k),
            }

    # Group cars by class
    cars_by_class = {}
    for k, info in user_cars.items():
        cls = info['class']
        cars_by_class.setdefault(cls, [])
        cars_by_class[cls].append({'key': k, 'name': info['name']})
    for cls in cars_by_class:
        cars_by_class[cls].sort(key=lambda x: x['name'])

    ordered_cars = [(cls, cars_by_class[cls]) for cls in CLASS_ORDER if cls in cars_by_class]

    tracks_used = sorted(
        {(s['track_key'], track_display_name(s['track_key'])) for s in setups},
        key=lambda x: x[1]
    )

    return render_template(
        'gap_report.html',
        ordered_cars=ordered_cars,
        tracks=tracks_used,
        covered=covered,
    )
