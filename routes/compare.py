"""Side-by-side setup comparison."""
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from supabase_client import svc_client
from routes.dashboard import login_required
from data.cars import car_display_name
from data.tracks import track_display_name

bp = Blueprint('compare', __name__)


@bp.get('/compare')
@login_required
def compare():
    user_id = session['user']['id']
    id_a = request.args.get('a', '').strip()
    id_b = request.args.get('b', '').strip()

    # If no IDs, show the picker UI
    if not id_a or not id_b:
        setups_res = svc_client.table('setups').select(
            'id, filename, car_key, car_name, track_key, track_name, setup_type, uploaded_at'
        ).eq('user_id', user_id).order('uploaded_at', desc=True).execute()
        setups = setups_res.data or []
        for s in setups:
            s['car_display']   = s.get('car_name') or car_display_name(s['car_key'])
            s['track_display'] = s.get('track_name') or track_display_name(s['track_key'])
        return render_template('compare_pick.html', setups=setups, id_a=id_a, id_b=id_b)

    # Load both setups and verify ownership
    res_a = svc_client.table('setups').select('id, filename, car_key, car_name, track_key, track_name, setup_type') \
        .eq('id', id_a).eq('user_id', user_id).maybe_single().execute()
    res_b = svc_client.table('setups').select('id, filename, car_key, car_name, track_key, track_name, setup_type') \
        .eq('id', id_b).eq('user_id', user_id).maybe_single().execute()

    if not res_a.data or not res_b.data:
        flash('One or both setups not found.', 'danger')
        return redirect(url_for('compare.compare'))

    setup_a = res_a.data
    setup_b = res_b.data

    for s in (setup_a, setup_b):
        s['car_display']   = s.get('car_name') or car_display_name(s['car_key'])
        s['track_display'] = s.get('track_name') or track_display_name(s['track_key'])

    # Load params for both setups
    params_res = svc_client.table('setup_params').select('setup_id, tab, section, label, value') \
        .in_('setup_id', [id_a, id_b]).execute()
    params = params_res.data or []

    # Build diff table: key=(tab, section, label) -> {a_val, b_val}
    diff_map = {}
    for p in params:
        key = (p.get('tab') or 'Other', p.get('section') or 'General', p['label'])
        diff_map.setdefault(key, {'a': None, 'b': None})
        if p['setup_id'] == id_a:
            diff_map[key]['a'] = p['value']
        else:
            diff_map[key]['b'] = p['value']

    # Organise into tabs > sections > rows
    tabs = {}
    diff_count = 0
    for (tab, section, label), vals in sorted(diff_map.items()):
        is_diff = vals['a'] != vals['b']
        if is_diff:
            diff_count += 1
        tabs.setdefault(tab, {}).setdefault(section, [])
        tabs[tab][section].append({
            'label':   label,
            'a':       vals['a'],
            'b':       vals['b'],
            'is_diff': is_diff,
        })

    return render_template(
        'compare.html',
        setup_a=setup_a,
        setup_b=setup_b,
        tabs=tabs,
        diff_count=diff_count,
    )
