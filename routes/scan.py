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
    r'[_\-](race|r|quali(fying)?|q|endurance|endu|end|wet|dry|baseline|'
    r'safe|default|oval|road|v\d+|\d+hr|practice|prac|test|hotlap|hl|'
    r'sprint|setup|fixed|open|multiclass|mc|imsa|gng|gng|gt|gtc|lmp|'
    r'no\d*|round\d*|week\d*|w\d+|s\d+|01|02|03|04|05|06|07|08|09|10|'
    r'11|12|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)$',
    re.IGNORECASE,
)

# Regex to remove leading season/week/series noise tokens before matching
# Matches things like: 25S3, 2025S2, W05, W09, GNG, IMSA, VRS, PMCD, EE
_NOISE_TOKEN_RE = re.compile(
    r'^(\d{2,4}s\d+|w\d+|gn?g|imsa|vrs|pmcd|ee|gt[34c]?|lmp[23]?|'
    r'gtp|gte|cup|pro|am|sr|jr|[a-z]{2,4}\d+)$',
    re.IGNORECASE,
)

# Aliases for common abbreviations not handled by fuzzy match
TRACK_ALIASES = {
    # Virginia
    'vir':              'virginia',
    'virginia':         'virginia',
    # Nürburgring
    'nords':            'nurburgring_nordschleife',
    'nordschleife':     'nurburgring_nordschleife',
    'nurb':             'nurburgring_gp',
    'nurburgring':      'nurburgring_gp',
    # Le Mans
    'lemans':           'le_mans',
    'le_mans':          'le_mans',
    'lemans24':         'le_mans',
    # Watkins Glen
    'watkins':          'watkins_glen',
    'glen':             'watkins_glen',
    # Daytona
    'daytona':          'daytona_road',
    'daytona24':        'daytona_road',
    # Sebring
    'sbr':              'sebring',
    'sebring12':        'sebring',
    # Road courses
    'road_atl':         'road_atlanta',
    'road_am':          'road_america',
    # Laguna Seca
    'laguna':           'laguna_seca',
    # Indianapolis
    'indy':             'indianapolis_road',
    'indianapolis':     'indianapolis_road',
    # Red Bull Ring
    'redbull':          'red_bull_ring',
    'red_bull':         'red_bull_ring',
    'rbr':              'red_bull_ring',
    # Phillip Island
    'phillip':          'phillip_island',
    # Paul Ricard
    'paul':             'paul_ricard',
    'ricard':           'paul_ricard',
    # Mid-Ohio
    'mid_oh':           'mid_ohio',
    'midohio':          'mid_ohio',
    # Lime Rock
    'limerock':         'lime_rock',
    'lime':             'lime_rock',
    # Long Beach
    'longbeach':        'long_beach',
    # Okayama (common misspelling)
    'okyama':           'okayama',
    'okayama':          'okayama',
    # Interlagos
    'interlagos':       'interlagos',
    # Brands Hatch
    'brands':           'brands_hatch',
    # Charlotte Roval
    'roval':            'charlotte_roval',
    'charlotte':        'charlotte_roval',
    # Oulton Park
    'oulton':           'oulton_park',
    # Phillip Island
    'phillip':          'phillip_island',
    # Suzuka
    'suzuka':           'suzuka',
    # Spa
    'spa':              'spa',
    'francorchamps':    'spa',
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


def _try_match(candidate: str) -> tuple[str, str, float]:
    """
    Try to match a single candidate string to a track key.
    Returns (track_key, track_name, confidence) or ('', '', 0.0).
    """
    if not candidate or len(candidate) < 3:
        return '', '', 0.0

    # Alias lookup
    if candidate in TRACK_ALIASES:
        key = TRACK_ALIASES[candidate]
        if key in TRACKS:
            return key, TRACKS[key]['name'], 1.0

    # Exact key match
    if candidate in TRACKS:
        return candidate, TRACKS[candidate]['name'], 1.0

    # Prefix/substring of a key (only when unambiguous)
    partial = [k for k in TRACKS if k.startswith(candidate) or candidate.startswith(k)]
    if len(partial) == 1:
        key = partial[0]
        ratio = difflib.SequenceMatcher(None, candidate, key).ratio()
        if ratio >= 0.65:
            return key, TRACKS[key]['name'], ratio

    # difflib fuzzy against all keys
    matches = difflib.get_close_matches(candidate, list(TRACKS.keys()), n=1, cutoff=0.6)
    if matches:
        key = matches[0]
        ratio = difflib.SequenceMatcher(None, candidate, key).ratio()
        return key, TRACKS[key]['name'], ratio

    # Match against significant words in display names
    for key, info in TRACKS.items():
        name_words = re.split(r'[\s\-()]+', info['name'].lower())
        for word in name_words:
            if len(word) >= 4 and word == candidate:
                return key, info['name'], 1.0

    return '', '', 0.0


def _fuzzy_match_track(stem: str) -> tuple[str, str, float]:
    """
    Try to match a filename stem to a track key by attempting the full
    cleaned stem, then every n-gram of tokens (1, 2, 3 tokens) extracted
    from the filename. Returns the highest-confidence result found.
    """
    # Normalise: hyphens, spaces, dots all become underscores
    normalized = stem.lower().replace('-', '_').replace(' ', '_').replace('.', '_')

    # Tokenise, then drop noise tokens (season codes, week numbers, series names)
    raw_tokens = [t for t in re.split(r'[_\s]+', normalized) if t]
    tokens = [t for t in raw_tokens if not _NOISE_TOKEN_RE.match(t) and len(t) >= 3]
    # Fall back to all tokens if filtering removed everything useful
    if not tokens:
        tokens = [t for t in raw_tokens if len(t) >= 3]

    # Build all candidates to try, in priority order:
    # 1. Full stem with suffixes stripped (using filtered tokens)
    # 2. All 3-token, 2-token, 1-token windows from the filtered token list
    filtered_stem = '_'.join(tokens)
    candidates = [_strip_suffixes(filtered_stem), _strip_suffixes(normalized)]
    for n in (3, 2, 1):
        for i in range(len(tokens) - n + 1):
            candidates.append('_'.join(tokens[i:i + n]))

    best_key, best_name, best_conf = '', '', 0.0
    for c in candidates:
        key, name, conf = _try_match(c)
        if conf > best_conf:
            best_key, best_name, best_conf = key, name, conf
        if best_conf == 1.0:
            break

    return best_key, best_name, best_conf


def _infer_setup_type(stem: str) -> str:
    s = stem.lower()
    if re.search(r'quali', s):
        return 'qualifying'
    if re.search(r'endur|endu\b', s):
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

        # Walk the car folder recursively to catch setups in subfolders
        try:
            sto_files = [
                (dirpath, f)
                for dirpath, _, files in os.walk(folder_path)
                for f in sorted(files)
                if f.lower().endswith('.sto')
            ]
        except PermissionError:
            continue

        for dirpath, filename in sto_files:
            if _already_imported(current_user.id, car_key, filename):
                skipped += 1
                continue

            stem = os.path.splitext(filename)[0]
            track_key, track_name, confidence = _fuzzy_match_track(stem)
            setup_type = _infer_setup_type(stem)

            items.append({
                'abs_path':        os.path.join(dirpath, filename),
                'filename':        filename,
                'car_key':         car_key,
                'car_name':        car_display,
                'car_class':       car_cls,
                'track_key':       track_key,
                'track_name':      track_name,
                'track_confidence': round(confidence, 2),
                'setup_type':      setup_type,
                'needs_review':    confidence < 0.65 or not track_key,
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
