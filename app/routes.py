from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm


@app.route('/')
@app.route('/index')
def index():
    user = {'username': 'Василий'}
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
    return render_template('index.html', title='Домашняя страница', user=user, posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash('Запрошенный логин для пользователя {}, запомнить меня={}'.format(form.username.data,
                                                                                form.remember_me.data))
        return redirect(url_for('index'))
    return render_template('login.html', title='Вход', form=form)
