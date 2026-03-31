from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from urllib.parse import urlparse, urljoin

from .extensions import db, bcrypt, limiter
from .models import User
from .forms import LoginForm, RegisterForm

auth_bp = Blueprint('auth', __name__)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=['POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    login_form = LoginForm()
    register_form = RegisterForm()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'register' and register_form.validate_on_submit():
            user = User.query.filter_by(username=register_form.username.data).first()
            if user:
                flash('Username already exists.', 'error')
            else:
                hashed_pw = bcrypt.generate_password_hash(register_form.password.data).decode('utf-8')
                new_user = User(username=register_form.username.data, password_hash=hashed_pw)
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user)
                flash('Account created successfully.', 'success')
                return redirect(url_for('main.dashboard'))
                
        elif action == 'login' and login_form.validate_on_submit():
            user = User.query.filter_by(username=login_form.username.data).first()
            if user and bcrypt.check_password_hash(user.password_hash, login_form.password.data):
                login_user(user)
                next_page = request.args.get('next')
                if not is_safe_url(next_page):
                    return abort(400)
                return redirect(next_page or url_for('main.dashboard'))
            else:
                flash('Invalid username or password.', 'error')
                
        # Handle form validation errors
        for form in [login_form, register_form]:
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{getattr(form, field).label.text}: {error}", 'error')

    return render_template('login.html', login_form=login_form, register_form=register_form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
