"""Generate signed download URL for a .sto file."""
from flask import Blueprint, redirect, session, flash, url_for
from supabase_client import svc_client
from routes.dashboard import login_required

bp = Blueprint('download', __name__)


@bp.get('/setups/<setup_id>/download')
@login_required
def download(setup_id):
    user_id = session['user']['id']

    res = svc_client.table('setups').select('storage_path, filename') \
        .eq('id', setup_id).eq('user_id', user_id).maybe_single().execute()

    if not res.data or not res.data.get('storage_path'):
        flash('Setup file not available for download.', 'danger')
        return redirect(url_for('setups.detail', setup_id=setup_id))

    storage_path = res.data['storage_path']

    try:
        signed = svc_client.storage.from_('setups').create_signed_url(storage_path, expires_in=60)
        url = signed.get('signedURL') or signed.get('signed_url') or signed.get('data', {}).get('signedUrl')
        if url:
            # Update last_used_at
            from datetime import datetime, timezone
            svc_client.table('setups').update({
                'last_used_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', setup_id).execute()
            return redirect(url)
    except Exception:
        pass

    flash('Could not generate download link. Please try again.', 'danger')
    return redirect(url_for('setups.detail', setup_id=setup_id))
