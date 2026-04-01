"""Auto-scan iRacing setups folder and bulk-import into the library."""
import os
import re
import json
import difflib
from flask import Blueprint, render_template, request, jsonify, Response, stream_with_context
from flask_login import login_required, current_user
from db import db
from models import Setup, SetupParam
from data.cars import CARS, car_display_name, car_class
from data.tracks import TRACKS, track_display_name
from routes.setups import _decode_sto, _extract_notes

bp = Blueprint('scan', __name__)

# Common filename suffixes to strip before track matching
_SUFFIX_RE = re.compile(
    r'[_\-](race|quali(fying)?|endurance|wet|dry|baseline|safe|default|'
    r'oval|road|v\d+|\d+hr|practice|prac|test|hotlap|hl|sprint|setup)$',
    re.IGNORECASE,
)

# Aliases for common abbreviations not handled by fuzzy match
TRACK_ALIASES = {
    'nords':            'nurburgring_nordschleife',
    'nordschleife':     'nurburgring_nordschleife',
    'nurb':             'nurburgring_gp',
    'nurburgring':      'nurburgring_gp',
    'lemans':           'le_mans',
    'le_mans':          'le_mans',
    'watkins':          'watkins_glen',
    'glen':             'watkins_glen',
    'road_atl':         'road_atlanta',
    'road_am':          'road_america',
    'laguna':           'laguna_seca',
    'indy':             'indianapolis_road',
    'indianapolis':     'indianapolis_road',
    'daytona':          'daytona_road',
    'redbull':          'red_bull_ring',
    'red_bull':         'red_bull_ring',
    'rbr':              'red_bull_ring',
    'phillip':          'phillip_island',
    'paul':             'paul_ricard',
    'ricard':           'paul_ricard',
    'mid_oh':           'mid_ohio',
    'midohio':          'mid_ohio',
    'limerock':         'lime_rock',
    'lime':             'lime_rock',
    'longbeach':        'long_beach',
    'sbr':              'sebring',
    'interlagos':       'interlagos',
}

# Lowercase car folder name → car_key (iRacing folder names match our keys)
_CAR_FOLDER_MAP = {k.lower(): k for k in CARS}


def _find_iracing_folder() -> str | None:
    """Return path to Documents\\iRacing\\setups if it exists."""
    candidates = [
        os.path.join(os.path.expanduser('~'), 'Documents', 'iRacing', 'setups'),
        os.path.join(os.environ.get('USERPROFILE', ''), 'Documents', 'iRacing', 'setups'),
        os.path.join(os.environ.get('ONEDRIVE', ''), 'Documents', 'iRacing', 'setups'),
    ]
    for path in candidates:
        if path and os.path.isdir(path):
            return path
    return None


def _strip_suffixes(stem: str) -> str:
    """Repeatedly strip known trailing tokens from a filename stem."""
    prev = None
    s = stem.lower().replace('-', '_').replace(' ', '_')
    while s != prev:
        prev = s
        s = _SUFFIX_RE.sub('', s)
    return s


def _fuzzy_match_track(stem: str) -> tuple[str, str, float]:
    """
    Try to match a filename stem to a track key.
    Returns (track_key, track_name, confidence) where confidence 0.0–1.0.
    """
    cleaned = _strip_suffixes(stem)

    # 1. Alias lookup
    if cleaned in TRACK_ALIASES:
        key = TRACK_ALIASES[cleaned]
        if key in TRACKS:
            return key, TRACKS[key]['name'], 1.0

    # 2. Exact key match
    if cleaned in TRACKS:
        return cleaned, TRACKS[cleaned]['name'], 1.0

    # 3. Partial key match (cleaned is a prefix/substring of a key)
    partial = [k for k in TRACKS if k.startswith(cleaned) or cleaned.startswith(k)]
    if len(partial) == 1:
        key = partial[0]
        ratio = difflib.SequenceMatcher(None, cleaned, key).ratio()
        if ratio >= 0.7:
            return key, TRACKS[key]['name'], ratio

    # 4. difflib fuzzy against all keys
    track_keys = list(TRACKS.keys())
    matches = difflib.get_close_matches(cleaned, track_keys, n=1, cutoff=0.55)
    if matches:
        key = matches[0]
        ratio = difflib.SequenceMatcher(None, cleaned, key).ratio()
        return key, TRACKS[key]['name'], ratio

    # 5. Match against display name words (e.g. 'spa' in 'Circuit de Spa-Francorchamps')
    for key, info in TRACKS.items():
        name_words = re.split(r'[\s\-()]+', info['name'].lower())
        for word in name_words:
            if len(word) >= 4 and (word == cleaned or cleaned.startswith(word) or word.startswith(cleaned)):
                ratio = difflib.SequenceMatcher(None, cleaned, word).ratio()
                if ratio >= 0.8:
                    return key, info['name'], ratio

    return '', '', 0.0


def _infer_setup_type(stem: str) -> str:
    s = stem.lower()
    if re.search(r'quali', s):
        return 'qualifying'
    if re.search(r'endur', s):
        return 'endurance'
    if re.search(r'wet', s):
        return 'wet'
    if re.search(r'baseline|default|safe', s):
        return 'baseline'
    return 'race'


def _already_imported(user_id: int, car_key: str, filename: str) -> bool:
    return Setup.query.filter_by(
        user_id=user_id, car_key=car_key, filename=filename
    ).first() is not None


@bp.get('/scan/detect-folder')
@login_required
def detect_folder():
    path = _find_iracing_folder()
    return jsonify({'path': path, 'exists': bool(path)})


@bp.post('/scan/start')
@login_required
def scan_start():
    setups_root = _find_iracing_folder()
    if not setups_root:
        return jsonify({'error': 'iRacing setups folder not found'}), 404

    items = []
    skipped = 0

    try:
        car_folders = os.listdir(setups_root)
    except PermissionError:
        return jsonify({'error': 'Permission denied reading setups folder'}), 403

    for folder_name in sorted(car_folders):
        folder_path = os.path.join(setups_root, folder_name)
        if not os.path.isdir(folder_path):
            continue

        car_key = _CAR_FOLDER_MAP.get(folder_name.lower(), folder_name.lower())
        car_display = car_display_name(car_key)
        car_cls = car_class(car_key)

        try:
            sto_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.sto')]
        except PermissionError:
            continue

        for filename in sorted(sto_files):
            if _already_imported(current_user.id, car_key, filename):
                skipped += 1
                continue

            stem = os.path.splitext(filename)[0]
            track_key, track_name, confidence = _fuzzy_match_track(stem)
            setup_type = _infer_setup_type(stem)

            items.append({
                'abs_path':        os.path.join(folder_path, filename),
                'filename':        filename,
                'car_key':         car_key,
                'car_name':        car_display,
                'car_class':       car_cls,
                'track_key':       track_key,
                'track_name':      track_name,
                'track_confidence': round(confidence, 2),
                'setup_type':      setup_type,
                'needs_review':    confidence < 0.75 or not track_key,
            })

    return jsonify({'found': len(items), 'skipped': skipped, 'items': items})


@bp.get('/scan/review')
@login_required
def scan_review():
    track_list = sorted(
        [{'key': k, 'name': v['name']} for k, v in TRACKS.items()],
        key=lambda x: x['name']
    )
    return render_template('scan_review.html', track_list=track_list)


@bp.post('/scan/stream')
@login_required
def scan_stream():
    """SSE endpoint: decode and import each setup, streaming progress back."""
    try:
        items = request.get_json(force=True) or []
    except Exception:
        return jsonify({'error': 'Invalid JSON'}), 400

    user_id = current_user.id

    def generate():
        imported = 0
        errors = 0

        for i, item in enumerate(items):
            abs_path   = item.get('abs_path', '')
            filename   = item.get('filename', '')
            car_key    = item.get('car_key', '')
            track_key  = item.get('track_key', '')
            setup_type = item.get('setup_type', 'race')

            # Skip if track not confirmed
            if not track_key:
                errors += 1
                yield _sse({'index': i, 'total': len(items), 'status': 'skip',
                            'filename': filename, 'reason': 'no_track'})
                continue

            # Skip duplicates that appeared between scan and import
            if _already_imported(user_id, car_key, filename):
                yield _sse({'index': i, 'total': len(items), 'status': 'skip',
                            'filename': filename, 'reason': 'already_imported'})
                continue

            # Read file
            try:
                with open(abs_path, 'rb') as f:
                    file_bytes = f.read()
            except Exception as e:
                errors += 1
                yield _sse({'index': i, 'total': len(items), 'status': 'error',
                            'filename': filename, 'reason': str(e)})
                continue

            # Decode via setupdelta
            decoded = _decode_sto(file_bytes, filename)
            if not decoded or not decoded.get('rows'):
                errors += 1
                yield _sse({'index': i, 'total': len(items), 'status': 'error',
                            'filename': filename, 'reason': 'decode_failed'})
                continue

            # Use API-confirmed car key if available
            api_car_key = decoded.get('carName') or car_key
            rows  = decoded['rows']
            notes = _extract_notes(file_bytes)

            car_disp  = car_display_name(api_car_key)
            car_cls   = car_class(api_car_key)
            track_disp = track_display_name(track_key)

            setup = Setup(
                user_id        = user_id,
                filename       = filename,
                car_name       = car_disp,
                car_key        = api_car_key,
                car_class      = car_cls,
                track_name     = track_disp,
                track_key      = track_key,
                setup_type     = setup_type,
                notes_text     = notes[:4000] if notes else None,
                decoded_params = json.dumps(rows),
                storage_path   = abs_path,  # point to original file in iRacing folder
            )
            db.session.add(setup)

            try:
                db.session.flush()
                params = [
                    SetupParam(
                        setup_id = setup.id,
                        user_id  = user_id,
                        tab      = row.get('tab'),
                        section  = row.get('section'),
                        label    = row.get('label', ''),
                        value    = row.get('metric_value', ''),
                    )
                    for row in rows if row.get('is_mapped')
                ]
                db.session.add_all(params)
                db.session.commit()
                imported += 1
                yield _sse({'index': i, 'total': len(items), 'status': 'ok',
                            'filename': filename, 'car': car_disp, 'track': track_disp,
                            'setup_id': setup.id})
            except Exception as e:
                db.session.rollback()
                errors += 1
                yield _sse({'index': i, 'total': len(items), 'status': 'error',
                            'filename': filename, 'reason': str(e)})

        yield _sse({'status': 'done', 'imported': imported, 'errors': errors})

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={'X-Accel-Buffering': 'no', 'Cache-Control': 'no-cache'},
    )


def _sse(data: dict) -> str:
    return f'data: {json.dumps(data)}\n\n'
