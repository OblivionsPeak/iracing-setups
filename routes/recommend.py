"""Setup recommendation and gap report."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Setup
from data.cars import car_display_name, car_class, all_cars_grouped, CLASS_ORDER
from data.tracks import track_display_name, TRACK_LIST, track_chars, similarity_score

bp = Blueprint('recommend', __name__)

_DF_ORDER  = ['low', 'medium', 'high', 'very_high']
_BR_ORDER  = ['light', 'medium', 'heavy']
_TS_ORDER  = ['low', 'medium', 'high']

_DF_LABEL = {'low': 'low downforce', 'medium': 'medium downforce',
             'high': 'high downforce', 'very_high': 'very high downforce'}
_BR_LABEL = {'light': 'light braking', 'medium': 'moderate braking', 'heavy': 'heavy braking'}
_TS_LABEL = {'low': 'easy on tyres', 'medium': 'moderate tyre stress', 'high': 'high tyre stress'}


def _find_best(setups, track_key):
    """
    Pick the best setup for track_key from the provided list.
    Returns (setup, reason, similarity_score, source_track_key).
    """
    # 1. Exact match
    exact = [s for s in setups if s.track_key == track_key]
    if exact:
        exact.sort(key=lambda s: (s.last_used_at or s.uploaded_at), reverse=True)
        return exact[0], 'exact_match', 1.0, track_key

    if not setups:
        return None, 'no_setups', 0.0, None

    # 2. Score every setup by track similarity, pick the best
    scored = []
    for s in setups:
        score = similarity_score(track_key, s.track_key)
        scored.append((score, s))
    scored.sort(key=lambda x: (-x[0], -(x[1].last_used_at or x[1].uploaded_at).timestamp()))

    best_score, best = scored[0]
    if best_score >= 0.85:
        reason = 'very_similar'
    elif best_score >= 0.6:
        reason = 'similar'
    else:
        reason = 'best_available'

    return best, reason, best_score, best.track_key


def _adjustment_advice(from_key: str, to_key: str) -> list[str]:
    """
    Return a list of specific, directional adjustment tips based on
    the characteristic differences between the source and target track.
    """
    src = track_chars(from_key)
    tgt = track_chars(to_key)
    if not src or not tgt:
        return []

    tips = []

    # Downforce
    si = _DF_ORDER.index(src['downforce'])
    ti = _DF_ORDER.index(tgt['downforce'])
    if ti < si:
        diff = si - ti
        adj = 'a little' if diff == 1 else 'significantly'
        tips.append(
            f"{track_display_name(to_key)} is a lower-downforce track — reduce front and rear wing {adj}. "
            f"Expect higher straight-line speed but less mechanical grip in corners."
        )
    elif ti > si:
        diff = ti - si
        adj = 'a little' if diff == 1 else 'significantly'
        tips.append(
            f"{track_display_name(to_key)} needs more downforce — add wing {adj}. "
            f"Prioritise corner speed over top speed."
        )

    # Braking
    bi_src = _BR_ORDER.index(src['braking'])
    bi_tgt = _BR_ORDER.index(tgt['braking'])
    if bi_tgt > bi_src:
        tips.append(
            f"Braking zones are harder here — move brake bias forward slightly and check brake duct settings."
        )
    elif bi_tgt < bi_src:
        tips.append(
            f"Lighter braking demands than your source setup — you may be able to soften brake bias or reduce cooling."
        )

    # Style
    if src['style'] != tgt['style']:
        style_map = {
            ('flowing', 'stop_go'):   "This is a more stop-go track — stiffen the suspension, raise ride height slightly, and run more mechanical grip.",
            ('stop_go', 'flowing'):   "This is a more flowing track — softer suspension and lower ride height will improve corner speed.",
            ('flowing', 'mixed'):     "More mixed character than your source track — check balance across slow and fast corners.",
            ('mixed', 'flowing'):     "More flowing than your source track — ride height and aero balance matter more than mechanical grip here.",
            ('stop_go', 'mixed'):     "Less stop-go than your source — you may not need as much low-speed mechanical grip.",
            ('mixed', 'stop_go'):     "More stop-go than your source track — prioritise traction and mechanical grip in slow corners.",
        }
        tip = style_map.get((src['style'], tgt['style']))
        if tip:
            tips.append(tip)

    # Tyre stress
    ts_src = _TS_ORDER.index(src['tire_stress'])
    ts_tgt = _TS_ORDER.index(tgt['tire_stress'])
    if ts_tgt > ts_src:
        tips.append(
            f"Higher tyre stress than your source track — consider increasing tyre pressures slightly "
            f"and check front-rear balance to avoid overheating one end."
        )
    elif ts_tgt < ts_src:
        tips.append(
            f"Lower tyre stress than your source track — you can afford to run slightly lower pressures for more grip."
        )

    # Bumps
    if tgt.get('bumpy') and not src.get('bumpy'):
        tips.append(
            "This track is bumpier than your source — soften slow-speed damper rebound and raise ride height "
            "to prevent bottoming out."
        )
    elif not tgt.get('bumpy') and src.get('bumpy'):
        tips.append(
            "This track is smoother — you can run a lower ride height and stiffer suspension without the bump penalty."
        )

    return tips


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
    best, reason, score, source_track = _find_best(setups, track_key)

    advice = []
    if reason != 'exact_match' and best and source_track:
        advice = _adjustment_advice(source_track, track_key)

    src_chars = track_chars(source_track) if source_track else {}
    tgt_chars = track_chars(track_key)

    return render_template(
        'recommend_result.html',
        car_display=car_display_name(car_key),
        track_display=track_display_name(track_key),
        best=best,
        reason=reason,
        score=round(score * 100),
        advice=advice,
        source_track=track_display_name(source_track) if source_track else None,
        src_chars=src_chars,
        tgt_chars=tgt_chars,
        car_key=car_key,
        track_key=track_key,
    )


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
