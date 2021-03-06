import os
from cProfile import Profile

from flask import flash, redirect, render_template, url_for, request
from flask_login import login_required, login_user, logout_user
from sqlalchemy import exc
from werkzeug.utils import secure_filename
from wtforms import ValidationError

from instance.config import UPLOAD_FOLDER
from . import auth
from .forms import RegistrationForm, LoginForm, Update
from ..__init___ import db
from ..gift_list.views import allowed_file, file_verification
from ..models import User


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    password=form.password.data)

        try:
            # add user to the database
            db.session.add(user)
            db.session.commit()
            flash('You have successfully registered! Now you can enter the site!')
        except:
            flash('An error occurred while registering, please try again ', 'danger')

        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form, title='Register')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            return redirect(f'/user_id:{user.id}/gift_list')

        else:
            flash('Wrong email address or password entered!', 'danger')
            return render_template('auth/login.html', form=form, title='Login')
    else:
        return render_template('auth/login.html', form=form, title='Login')


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have successfully logged out!')
    return redirect(url_for('auth.login'))


@auth.route('/user_id:<int:id>/update', methods=['POST', 'GET'])
def user_update(id):
    form = Update()
    user = User.query.get(id)
    if form.validate_on_submit() or request.method == 'POST':

        if form.img.data:
            if allowed_file(form.img.data.filename):
                if user.images_path is not None:
                    os.remove(f'{UPLOAD_FOLDER}\\{user.images_path}')
                f = form.img.data
                filename = file_verification(user.id, secure_filename(f.filename))
                if filename:
                    f.save(os.path.join(UPLOAD_FOLDER, filename))
                    user.images_path = filename
                else:
                    user.images_path = None
            else:
                flash('Invalid format', 'danger')
                user.images_path = None
                return render_template('auth/update.html', form=form, user=user)

        if form.password.data:
            if user.verify_password(form.old_password.data):
                user.password = form.password.data
            else:
                flash('Old password is incorrect', 'danger')
                return render_template('auth/update.html', form=form, user=user)

        try:
            user.email = form.email.data
            user.username = form.username.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            db.session.commit()
            flash('Changes saved!')
            return redirect(url_for('gift_list.index'))

        except exc.IntegrityError:
            db.session.rollback()
            return render_template('auth/update.html', form=form, user=user)

    else:
        form.email.data = user.email
        form.username.data = user.username
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
        return render_template('auth/update.html', form=form, user=user)
