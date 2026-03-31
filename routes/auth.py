"""Login, signup, logout, password reset."""
import os
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from supabase_client import anon_client, svc_client

bp = Blueprint('auth', __name__)


@bp.get('/login')
def login_page():
    if session.get('user'):
        return redirect(url_for('dashboard.home'))
    return render_template('login.html')


@bp.post('/login')
def login():
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    try:
        res = anon_client.auth.sign_in_with_password({'email': email, 'password': password})
        session['user']         = {'id': res.user.id, 'email': res.user.email}
        session['access_token'] = res.session.access_token
        return redirect(url_for('dashboard.home'))
    except Exception:
        flash('Invalid email or password.', 'danger')
        return render_template('login.html', email=email)


@bp.get('/signup')
def signup_page():
    if session.get('user'):
        return redirect(url_for('dashboard.home'))
    return render_template('signup.html')


@bp.post('/signup')
def signup():
    email    = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    confirm  = request.form.get('confirm', '')
    name     = request.form.get('display_name', '').strip()

    if password != confirm:
        flash('Passwords do not match.', 'danger')
        return render_template('signup.html', email=email, display_name=name)
    if len(password) < 8:
        flash('Password must be at least 8 characters.', 'danger')
        return render_template('signup.html', email=email, display_name=name)

    try:
        res = anon_client.auth.sign_up({'email': email, 'password': password})
        user_id = res.user.id
        svc_client.table('profiles').upsert({
            'id': user_id,
            'display_name': name or email.split('@')[0],
        }).execute()
        session['user']         = {'id': user_id, 'email': res.user.email}
        session['access_token'] = res.session.access_token if res.session else None
        flash('Account created! Welcome to iRacing Setups.', 'success')
        return redirect(url_for('dashboard.home'))
    except Exception:
        flash('Could not create account. That email may already be registered.', 'danger')
        return render_template('signup.html', email=email, display_name=name)


@bp.get('/logout')
def logout():
    try:
        anon_client.auth.sign_out()
    except Exception:
        pass
    session.clear()
    return redirect(url_for('index'))


@bp.get('/auth/forgot')
def forgot_page():
    if session.get('user'):
        return redirect(url_for('dashboard.home'))
    return render_template('forgot_password.html')


@bp.post('/auth/forgot')
def forgot_send():
    email   = request.form.get('email', '').strip()
    app_url = os.environ.get('APP_URL', '')
    if email:
        try:
            anon_client.auth.reset_password_for_email(
                email,
                options={'redirect_to': f'{app_url}/auth/reset'},
            )
        except Exception:
            pass
    flash("If that email is registered, you'll receive a reset link shortly.", 'info')
    return redirect(url_for('auth.forgot_page'))


@bp.get('/auth/reset')
def reset_page():
    return render_template('reset_password.html')


@bp.post('/auth/reset')
def reset_do():
    token   = request.form.get('token', '').strip()
    new_pw  = request.form.get('new_password', '')
    confirm = request.form.get('confirm_password', '')

    if not token:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.forgot_page'))
    if new_pw != confirm:
        flash('Passwords do not match.', 'danger')
        return redirect(url_for('auth.reset_page'))
    if len(new_pw) < 8:
        flash('Password must be at least 8 characters.', 'danger')
        return redirect(url_for('auth.reset_page'))

    try:
        user_resp = anon_client.auth.get_user(token)
        svc_client.auth.admin.update_user_by_id(user_resp.user.id, {'password': new_pw})
        flash('Password updated. Please log in.', 'success')
        return redirect(url_for('auth.login_page'))
    except Exception:
        flash('Reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_page'))
