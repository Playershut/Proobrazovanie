from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from urllib.parse import urlsplit
from app import app, db
from app.models import Teacher, Subject
from app.forms import LoginForm, RegistrationForm


@app.route('/')
@app.route('/index')
@login_required
def index():
    posts = [
        {
            'author': {'username': 'Иван'},
            'body': 'Поурочный план №1 Математика'
        },
        {
            'author': {'username': 'Александр'},
            'body': 'Поурочный план №2 Русский язык'
        },
        {
            'author': {'username': 'Иван'},
            'body': 'Поурочный план №3 Физика'
        }
    ]
    return render_template('index.html', title='Домашняя страница', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(Teacher).where(Teacher.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Неверный логин или пароль')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Вход', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('/index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = Teacher(username=form.username.data,
                       email=form.email.data,
                       full_name=form.full_name.data,
                       about=form.about.data,
                       educational_institution=form.educational_institution.data)
        user.set_password(form.password.data)
        user.subjects = db.session.query(Subject).filter(Subject.id.in_(form.subjects.data)).all()
        db.session.add(user)
        db.session.commit()
        flash('Поздравляем, теперь Вы зарегистрированный пользователь')
        return redirect(url_for('index'))
    return render_template('register.html', title='Регистрация', form=form)
