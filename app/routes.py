from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
import sqlalchemy as sa
from urllib.parse import urlsplit
from app import app, db
from app.email import send_password_reset_email
from app.models import Teacher, Subject, Page, Review
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PageAddForm, ReviewAddForm, EditPageForm, \
    ResetPasswordRequestForm, ResetPasswordForm


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Page).order_by(Page.timestamp.desc())
    posts = db.paginate(query, page=page, per_page=app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('index', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Домашняя страница', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


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


@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(Teacher).where(Teacher.username == username))
    page = request.args.get('page', 1, type=int)
    query = user.pages.select().order_by(Page.timestamp.desc())
    posts = db.paginate(query, page=page,
                        per_page=app.config['POSTS_PER_PAGE'],
                        error_out=False)
    next_url = url_for('user', username=user.username, page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('user.html', user=user, title='Профиль {}'.format(username), posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.full_name = form.full_name.data
        current_user.about = form.about.data
        current_user.educational_institution = form.educational_institution.data
        current_user.subjects = db.session.query(Subject).filter(Subject.id.in_(form.subjects.data)).all()
        db.session.commit()
        flash('Ваши изменения сохранены.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.full_name.data = current_user.full_name
        form.about.data = current_user.about
        form.educational_institution.data = str(current_user.educational_institution)
        form.subjects.data = [str(s.id) for s in current_user.subjects]
    return render_template('edit_profile.html', title='Редактирование профиля', form=form)


@app.route('/explore')
@login_required
def explore():
    page = request.args.get('page', 1, type=int)
    query = sa.select(Page).order_by(Page.timestamp.desc())
    posts = db.paginate(query, page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('explore', page=posts.next_num) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num) \
        if posts.has_prev else None
    return render_template('index.html', title='Исследование', posts=posts.items,
                           next_url=next_url, prev_url=prev_url)


@app.route('/add_page')
@login_required
def add_page():
    form = PageAddForm()
    if form.validate_on_submit():
        post = Page(name=form.name.data,
                    description=form.description.data,
                    grade=form.grade.data,
                    type_of_work=form.type_of_work.data,
                    subject=form.subject.data,
                    author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Вы выложили статью!')
        return redirect(url_for('index'))
    return render_template('add_page.html', title='Добавление статьи', form=form)


@app.route('/page/<id>', methods=['GET', 'POST'])
@login_required
def page(id):
    form = ReviewAddForm()
    page = db.first_or_404(sa.select(Page).where(Page.id == id))

    review_id = request.args.get('delete', 0, type=int)
    review = Review.query.get(review_id)
    if review and review.author == current_user and review.page == page:
        db.session.delete(review)
        db.session.commit()
        flash('Отзыв был удалён')

    reviews_adding_visibility = page.author != current_user and all([r.author != current_user for r in page.reviews])
    if form.validate_on_submit():
        review = Review(rate=form.rate.data,
                        comment=form.comment.data,
                        author=current_user,
                        page=page)
        db.session.add(review)
        db.session.commit()
        reviews = page.reviews
        page.average_rating = sum([r.rate for r in reviews]) / len(reviews)
        db.session.commit()
        flash('Вы оставили отзыв')
        return redirect(url_for('page', id=page.id))
    return render_template('page.html', page=page, title=page.name, form=form, reviews=page.reviews,
                           rav=reviews_adding_visibility)


@app.route('/edit_page/<id>', methods=['GET', 'POST'])
@login_required
def edit_page(id):
    page = db.first_or_404(sa.select(Page).where(Page.id == id).where(Page.author == current_user))
    form = EditPageForm()
    if form.validate_on_submit():
        page.name = form.name.data
        page.description = form.description.data
        page.grade = form.grade.data
        page.type_of_work = form.type_of_work.data
        page.subject = form.subject.data
        db.session.commit()
        flash('Ваши изменения сохранены.')
        return redirect(url_for('edit_page', id=page.id))
    elif request.method == 'GET':
        form.name.data = page.name
        form.description.data = page.description
        form.grade.data = str(page.grade)
        form.type_of_work.data = str(page.type_of_work)
        form.subject.data = str(page.subject)
    return render_template('edit_page.html', title='Редактирование статьи', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(Teacher).where(Teacher.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash('Проверьте Вашу электронную почту для инструкций по сбросу пароля')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Сброс пароля', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = Teacher.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Ваш пароль был сброшен.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)
