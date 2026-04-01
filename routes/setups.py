"""Upload, browse, detail, delete setups."""
import os
import re
import json
import requests as req
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from db import db
from models import Setup, SetupParam
from data.cars import car_display_name, car_class
from data.tracks import track_display_name, TRACK_LIST

bp = Blueprint('setups', __name__)

SETUPDELTA_API     = 'https://www.setupdelta.com/api/setup/decode'
SETUPDELTA_TIMEOUT = 20


def _decode_sto(file_bytes: bytes, filename: str) -> dict | None:
    """
    Returns decoded dict on success, or None on failure.
    On API error, attaches '_status_code' to None — callers can inspect
    by calling _decode_sto_verbose instead.
    """
    result, _ = _decode_sto_verbose(file_bytes, filename)
    return result


def _decode_sto_verbose(file_bytes: bytes, filename: str) -> tuple[dict | None, int]:
    """Returns (decoded_dict_or_None, http_status_code). 0 = network/timeout error."""
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
            return resp.json(), 200
        return None, resp.status_code
    except req.exceptions.Timeout:
        return None, 0
    except Exception:
        return None, 0


def _extract_notes(file_bytes: bytes) -> str:
    try:
        for i in range(16, len(file_bytes) - 4):
            if (file_bytes[i] < 128 and file_bytes[i+1] == 0 and
                    file_bytes[i+2] < 128 and file_bytes[i+3] == 0 and
                    32 <= file_bytes[i] < 127 and 32 <= file_bytes[i+2] < 127):
                raw = file_bytes[i:].rstrip(b'\x00')
                return raw.decode('utf-16-le', errors='replace').strip()
    except Exception:
        pass
    return ''


@bp.get('/setups/upload')
@login_required
def upload_page():
    return render_template('setup_upload.html', track_list=TRACK_LIST)


@bp.post('/setups/upload')
@login_required
def upload():
    sto_file   = request.files.get('sto_file')
    track_key  = request.form.get('track_key', '').strip()
    track_name = request.form.get('track_name', '').strip()
    setup_type = request.form.get('setup_type', 'race').strip()

    if not sto_file or not sto_file.filename.endswith('.sto'):
        flash('Please select a valid .sto file.', 'danger')
        return redirect(url_for('setups.upload_page'))
    if not track_key:
        flash('Please select a track.', 'danger')
        return redirect(url_for('setups.upload_page'))

    file_bytes = sto_file.read()
    filename   = sto_file.filename

    decoded = _decode_sto(file_bytes, filename)
    if not decoded or not decoded.get('rows'):
        flash('Could not decode this setup file. Make sure it is a valid iRacing .sto file.', 'danger')
        return redirect(url_for('setups.upload_page'))

    car_key = decoded.get('carName', 'unknown')
    rows    = decoded['rows']
    notes   = _extract_notes(file_bytes)

    setup = Setup(
        user_id        = current_user.id,
        filename       = filename,
        car_name       = car_display_name(car_key),
        car_key        = car_key,
        car_class      = car_class(car_key),
        track_name     = track_name or track_display_name(track_key),
        track_key      = track_key,
        setup_type     = setup_type,
        notes_text     = notes[:4000] if notes else None,
        decoded_params = json.dumps(rows),
    )
    db.session.add(setup)
    db.session.flush()  # get setup.id before committing

    # Save .sto file to disk
    upload_folder = current_app.config['UPLOAD_FOLDER']
    user_folder   = os.path.join(upload_folder, str(current_user.id))
    os.makedirs(user_folder, exist_ok=True)
    storage_path  = os.path.join(user_folder, f'{setup.id}.sto')
    try:
        with open(storage_path, 'wb') as f:
            f.write(file_bytes)
        setup.storage_path = storage_path
    except Exception:
        pass  # App still works without the file

    # Bulk insert setup_params
    params = []
    for row in rows:
        if row.get('is_mapped'):
            params.append(SetupParam(
                setup_id = setup.id,
                user_id  = current_user.id,
                tab      = row.get('tab'),
                section  = row.get('section'),
                label    = row.get('label', ''),
                value    = row.get('metric_value', ''),
            ))
    db.session.add_all(params)
    db.session.commit()

    flash(f'Uploaded: {car_display_name(car_key)} at {track_display_name(track_key)}.', 'success')
    return redirect(url_for('setups.detail', setup_id=setup.id))


@bp.get('/setups')
@login_required
def list_setups():
    car_filter   = request.args.get('car', '')
    track_filter = request.args.get('track', '')
    class_filter = request.args.get('class', '')

    query = Setup.query.filter_by(user_id=current_user.id)
    if car_filter:
        query = query.filter_by(car_key=car_filter)
    if track_filter:
        query = query.filter_by(track_key=track_filter)
    if class_filter:
        query = query.filter_by(car_class=class_filter)

    setups = query.order_by(Setup.uploaded_at.desc()).all()

    all_cars   = sorted({(s.car_key, s.car_name) for s in setups}, key=lambda x: x[1])
    all_tracks = sorted({(s.track_key, s.track_name) for s in setups}, key=lambda x: x[1])
    all_classes = sorted({s.car_class for s in setups})

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
    setup = Setup.query.filter_by(id=setup_id, user_id=current_user.id).first_or_404()

    rows = setup.get_decoded_params()
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

    return render_template('setup_detail.html', setup=setup, tabs=tabs, unmapped=unmapped)


@bp.post('/api/advisor-notes')
@login_required
def advisor_notes():
    """
    Called by the Setup Advisor to append telemetry-based recommendations
    to the most recent matching setup in the library.
    Accepts JSON: {car_key, track_key, notes}
    """
    data      = request.get_json(force=True) or {}
    car_key   = data.get('car_key', '').strip()
    track_key = data.get('track_key', '').strip()
    notes     = data.get('notes', '').strip()

    if not car_key or not track_key or not notes:
        return jsonify({'error': 'car_key, track_key and notes are required'}), 400

    setup = (Setup.query
             .filter_by(user_id=current_user.id, car_key=car_key, track_key=track_key)
             .order_by(Setup.uploaded_at.desc())
             .first())

    if not setup:
        return jsonify({'error': 'No matching setup found in library'}), 404

    from datetime import datetime
    header = f'\n\n--- Advisor notes ({datetime.utcnow().strftime("%Y-%m-%d %H:%M")} UTC) ---\n'
    existing = setup.notes_text or ''
    setup.notes_text = (existing + header + notes)[:8000]
    db.session.commit()

    return jsonify({'ok': True, 'setup_id': setup.id, 'setup_filename': setup.filename})


@bp.post('/setups/<setup_id>/delete')
@login_required
def delete(setup_id):
    setup = Setup.query.filter_by(id=setup_id, user_id=current_user.id).first_or_404()

    if setup.storage_path and os.path.exists(setup.storage_path):
        try:
            os.remove(setup.storage_path)
        except Exception:
            pass

    db.session.delete(setup)
    db.session.commit()
    flash('Setup deleted.', 'success')
    return redirect(url_for('setups.list_setups'))
