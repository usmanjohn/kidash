from flask import Blueprint, render_template, redirect, url_for, flash
from .forms import RegistrationForm, LoginForm
from models.models import User
from extensions.extensions import db, bcrypt
from flask_login import login_user, current_user, logout_user


users = Blueprint('users', __name__, template_folder='templates')

@users.route('/register', methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('users.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash(f'Account created for {form.username.data}, You can login now!' , 'success')
        return redirect(url_for('users.login'))  # Ensure it refers to 'users.login'
    return render_template('register.html', title='Register', form=form)

@users.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('uploads.home'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            flash('You are logged in!', 'success')
            return redirect(url_for('uploads.home'))
        else:
            flash('Login Unsuccessful, Please check email and password', 'danger')
            return redirect(url_for('users.login'))
        return redirect(url_for('users.home'))  # Ensure it refers to 'users.home'
    return render_template('login.html', title='Login', form=form)

@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('uploads.home'))

