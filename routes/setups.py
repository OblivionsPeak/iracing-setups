"""Upload, browse, detail, delete setups."""
import re
import requests as req
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from supabase_client import svc_client
from routes.dashboard import login_required
from data.cars import car_display_name, car_class, all_cars_grouped, CARS
from data.tracks import track_display_name, TRACK_LIST

bp = Blueprint('setups', __name__)

SETUPDELTA_API = 'https://www.setupdelta.com/api/setup/decode'
SETUPDELTA_TIMEOUT = 20  # seconds


def _slugify(s: str) -> str:
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


def _decode_sto(file_bytes: bytes, filename: str) -> dict | None:
    """Call setupdelta API and return parsed JSON, or None on failure."""
    try:
        resp = req.post(
            SETUPDELTA_API,
            files={'file': (filename, file_bytes, 'application/octet-stream')},
            headers={
                'Origin':  'https://www.setupdelta.com',
                'Referer': 'https://www.setupdelta.com/',
            },
            timeout=SETUPDELTA_TIMEOUT,
        )
        if resp.status_code == 200:
            return resp.json()
    except req.exceptions.Timeout:
        pass
    except Exception:
        pass
    return None


def _extract_notes(file_bytes: bytes) -> str:
    """Extract the UTF-16 LE notes/description from a .sto file."""
    try:
        # Find the UTF-16 text section (wide chars)
        for i in range(16, len(file_bytes) - 4):
            if (file_bytes[i] < 128 and file_bytes[i+1] == 0 and
                    file_bytes[i+2] < 128 and file_bytes[i+3] == 0 and
                    32 <= file_bytes[i] < 127 and 32 <= file_bytes[i+2] < 127):
                raw = file_bytes[i:]
                # Trim trailing nulls
                raw = raw.rstrip(b'\x00')
                return raw.decode('utf-16-le', errors='replace').strip()
    except Exception:
        pass
    return ''


def _build_params(rows: list, setup_id: str, user_id: str) -> list:
    """Convert setupdelta rows to setup_params records."""
    params = []
    for row in rows:
        val = row.get('metric_value', '')
        params.append({
            'setup_id':  setup_id,
            'user_id':   user_id,
            'tab':       row.get('tab'),
            'section':   row.get('section'),
            'label':     row.get('label', ''),
            'value':     val,
        })
    return params


@bp.get('/setups/upload')
@login_required
def upload_page():
    return render_template('setup_upload.html', track_list=TRACK_LIST, cars=all_cars_grouped())


@bp.post('/setups/upload')
@login_required
def upload():
    user_id  = session['user']['id']
    sto_file = request.files.get('sto_file')
    track_key   = request.form.get('track_key', '').strip()
    track_name  = request.form.get('track_name', '').strip()
    setup_type  = request.form.get('setup_type', 'race').strip()

    if not sto_file or not sto_file.filename.endswith('.sto'):
        flash('Please select a valid .sto file.', 'danger')
        return redirect(url_for('setups.upload_page'))
    if not track_key:
        flash('Please select a track.', 'danger')
        return redirect(url_for('setups.upload_page'))

    file_bytes = sto_file.read()
    filename   = sto_file.filename

    # Decode via setupdelta
    decoded = _decode_sto(file_bytes, filename)
    if not decoded or not decoded.get('rows'):
        flash('Could not decode this setup file. Please check it is a valid iRacing .sto file.', 'danger')
        return redirect(url_for('setups.upload_page'))

    car_key  = decoded.get('carName', 'unknown')
    rows     = decoded['rows']
    notes    = _extract_notes(file_bytes)

    # Insert setup row first to get the ID
    insert_res = svc_client.table('setups').insert({
        'user_id':        user_id,
        'filename':       filename,
        'car_name':       car_display_name(car_key),
        'car_key':        car_key,
        'car_class':      car_class(car_key),
        'track_name':     track_name or track_display_name(track_key),
        'track_key':      track_key,
        'setup_type':     setup_type,
        'notes_text':     notes[:4000] if notes else None,
        'decoded_params': rows,
    }).execute()

    if not insert_res.data:
        flash('Database error saving setup. Please try again.', 'danger')
        return redirect(url_for('setups.upload_page'))

    setup_id     = insert_res.data[0]['id']
    storage_path = f'{user_id}/{setup_id}.sto'

    # Upload .sto to Supabase Storage
    try:
        svc_client.storage.from_('setups').upload(
            path=storage_path,
            file=file_bytes,
            file_options={'content-type': 'application/octet-stream'},
        )
    except Exception:
        # Storage upload failed — still usable, just no download
        pass

    # Update storage_path
    svc_client.table('setups').update({'storage_path': storage_path}).eq('id', setup_id).execute()

    # Bulk insert setup_params
    params = _build_params(rows, setup_id, user_id)
    if params:
        # Insert in chunks of 100
        for i in range(0, len(params), 100):
            svc_client.table('setup_params').insert(params[i:i+100]).execute()

    flash(f'Setup uploaded: {car_display_name(car_key)} at {track_display_name(track_key)}.', 'success')
    return redirect(url_for('setups.detail', setup_id=setup_id))


@bp.get('/setups')
@login_required
def list_setups():
    user_id   = session['user']['id']
    car_filter   = request.args.get('car', '')
    track_filter = request.args.get('track', '')
    class_filter = request.args.get('class', '')

    query = svc_client.table('setups').select(
        'id, filename, car_name, car_key, car_class, track_name, track_key, setup_type, uploaded_at, last_used_at'
    ).eq('user_id', user_id)

    if car_filter:
        query = query.eq('car_key', car_filter)
    if track_filter:
        query = query.eq('track_key', track_filter)
    if class_filter:
        query = query.eq('car_class', class_filter)

    setups_res = query.order('uploaded_at', desc=True).execute()
    setups = setups_res.data or []

    # Enrich with display names
    for s in setups:
        s['car_display']   = s.get('car_name') or car_display_name(s['car_key'])
        s['track_display'] = s.get('track_name') or track_display_name(s['track_key'])

    # Build filter options from user's actual data
    all_cars   = sorted({(s['car_key'], s['car_display']) for s in setups}, key=lambda x: x[1])
    all_tracks = sorted({(s['track_key'], s['track_display']) for s in setups}, key=lambda x: x[1])
    all_classes = sorted({s['car_class'] for s in setups})

    return render_template(
        'setup_list.html',
        setups=setups,
        all_cars=all_cars,
        all_tracks=all_tracks,
        all_classes=all_classes,
        car_filter=car_filter,
        track_filter=track_filter,
        class_filter=class_filter,
    )


@bp.get('/setups/<setup_id>')
@login_required
def detail(setup_id):
    user_id = session['user']['id']
    res = svc_client.table('setups').select('*').eq('id', setup_id).eq('user_id', user_id).maybe_single().execute()
    if not res.data:
        flash('Setup not found.', 'danger')
        return redirect(url_for('setups.list_setups'))

    setup = res.data
    setup['car_display']   = car_display_name(setup['car_key'])
    setup['track_display'] = track_display_name(setup['track_key'])

    # Group params by tab > section
    rows = setup.get('decoded_params') or []
    tabs = {}
    unmapped = []
    for row in rows:
        if not row.get('is_mapped'):
            unmapped.append(row)
            continue
        tab  = row.get('tab') or 'Other'
        sect = row.get('section') or 'General'
        tabs.setdefault(tab, {}).setdefault(sect, [])
        tabs[tab][sect].append(row)

    return render_template(
        'setup_detail.html',
        setup=setup,
        tabs=tabs,
        unmapped=unmapped,
    )


@bp.post('/setups/<setup_id>/delete')
@login_required
def delete(setup_id):
    user_id = session['user']['id']
    res = svc_client.table('setups').select('storage_path').eq('id', setup_id).eq('user_id', user_id).maybe_single().execute()
    if not res.data:
        flash('Setup not found.', 'danger')
        return redirect(url_for('setups.list_setups'))

    storage_path = res.data.get('storage_path')
    if storage_path:
        try:
            svc_client.storage.from_('setups').remove([storage_path])
        except Exception:
            pass

    svc_client.table('setups').delete().eq('id', setup_id).eq('user_id', user_id).execute()
    flash('Setup deleted.', 'success')
    return redirect(url_for('setups.list_setups'))
