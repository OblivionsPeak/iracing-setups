"""Login, signup, logout."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from db import db
from models import User

bp = Blueprint('auth', __name__)


@bp.get('/login')
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    return render_template('login.html')


@bp.post('/login')
def login():
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        login_user(user)
        return redirect(url_for('dashboard.home'))
    flash('Invalid email or password.', 'danger')
    return render_template('login.html', email=email)


@bp.get('/signup')
def signup_page():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.home'))
    return render_template('signup.html')


@bp.post('/signup')
def signup():
    email    = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '')
    confirm  = request.form.get('confirm', '')
    name     = request.form.get('display_name', '').strip()

    if password != confirm:
        flash('Passwords do not match.', 'danger')
        return render_template('signup.html', email=email, display_name=name)
    if len(password) < 8:
        flash('Password must be at least 8 characters.', 'danger')
        return render_template('signup.html', email=email, display_name=name)
    if User.query.filter_by(email=email).first():
        flash('That email is already registered.', 'danger')
        return render_template('signup.html', email=email, display_name=name)

    user = User(email=email, display_name=name or email.split('@')[0])
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    login_user(user)
    flash('Account created! Welcome to iRacing Setups.', 'success')
    return redirect(url_for('dashboard.home'))


@bp.get('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@bp.get('/auth/forgot')
def forgot_page():
    return render_template('forgot_password.html')
