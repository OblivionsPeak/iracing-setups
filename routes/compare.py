"""Side-by-side setup comparison."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import Setup, SetupParam

bp = Blueprint('compare', __name__)


@bp.get('/compare')
@login_required
def compare():
    id_a = request.args.get('a', '').strip()
    id_b = request.args.get('b', '').strip()

    if not id_a or not id_b:
        setups = Setup.query.filter_by(user_id=current_user.id) \
            .order_by(Setup.uploaded_at.desc()).all()
        return render_template('compare_pick.html', setups=setups, id_a=id_a, id_b=id_b)

    setup_a = Setup.query.filter_by(id=id_a, user_id=current_user.id).first()
    setup_b = Setup.query.filter_by(id=id_b, user_id=current_user.id).first()

    if not setup_a or not setup_b:
        flash('One or both setups not found.', 'danger')
        return redirect(url_for('compare.compare'))

    params = SetupParam.query.filter(
        SetupParam.setup_id.in_([id_a, id_b]),
        SetupParam.user_id == current_user.id,
    ).all()

    # Build diff map keyed by (tab, section, label)
    diff_map = {}
    for p in params:
        key = (p.tab or 'Other', p.section or 'General', p.label)
        diff_map.setdefault(key, {'a': None, 'b': None})
        if p.setup_id == id_a:
            diff_map[key]['a'] = p.value
        else:
            diff_map[key]['b'] = p.value

    tabs = {}
    diff_count = 0
    for (tab, section, label), vals in sorted(diff_map.items()):
        is_diff = vals['a'] != vals['b']
        if is_diff:
            diff_count += 1
        tabs.setdefault(tab, {}).setdefault(section, [])
        tabs[tab][section].append({
            'label': label, 'a': vals['a'], 'b': vals['b'], 'is_diff': is_diff,
        })

    return render_template(
        'compare.html',
        setup_a=setup_a,
        setup_b=setup_b,
        tabs=tabs,
        diff_count=diff_count,
    )
