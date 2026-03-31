"""Serve .sto file download directly from disk."""
import os
from datetime import datetime, timezone
from flask import Blueprint, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
from db import db
from models import Setup

bp = Blueprint('download', __name__)


@bp.get('/setups/<setup_id>/download')
@login_required
def download(setup_id):
    setup = Setup.query.filter_by(id=setup_id, user_id=current_user.id).first_or_404()

    if not setup.storage_path or not os.path.exists(setup.storage_path):
        flash('File not available for download. The .sto file may not have been saved.', 'danger')
        return redirect(url_for('setups.detail', setup_id=setup_id))

    setup.last_used_at = datetime.now(timezone.utc)
    db.session.commit()

    return send_file(
        setup.storage_path,
        as_attachment=True,
        download_name=setup.filename,
        mimetype='application/octet-stream',
    )
