import os
import uuid
from urllib.parse import urlsplit

import sqlalchemy as sa
from PIL import Image
from flask import render_template, flash, redirect, url_for, request, current_app, abort, send_from_directory
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import or_, func
from werkzeug.utils import secure_filename

from app import app, db
from app.email import send_password_reset_email
from app.forms import LoginForm, RegistrationForm, EditProfileForm, PageAddForm, ReviewAddForm, EditPageForm, \
    ResetPasswordRequestForm, ResetPasswordForm, SearchForm, EmptyForm

from app.models import Teacher, Subject, Page, Review


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def generate_unique_filename(filename):
    _, ext = os.path.splitext(filename)
    return uuid.uuid4().hex + ext


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
    next_url = url_for('user', username=user.username, page=posts.next_num) if posts.has_next else None
    prev_url = url_for('user', username=user.username, page=posts.prev_num) if posts.has_prev else None
    form = EmptyForm()  # 👈 добавлено
    return render_template('user.html', user=user, title='Профиль {}'.format(username), posts=posts.items,
                           next_url=next_url, prev_url=prev_url, form=form, followed=user.followed.all())  # 👈 form добавлен


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        if form.avatar.data:
            image_file = form.avatar.data

            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            file_extension = image_file.filename.rsplit('.', 1)[1].lower()
            if file_extension not in allowed_extensions:
                flash('Разрешены только изображения в форматах PNG, JPG, JPEG, GIF.')
                return redirect(url_for('edit_profile'))

            from flask import current_app
            avatar_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
            os.makedirs(avatar_dir, exist_ok=True)

            base_filename = current_user.username

            for ext in allowed_extensions:
                old_avatar_path = os.path.join(avatar_dir, f"{base_filename}.{ext}")
                if os.path.exists(old_avatar_path):
                    os.remove(old_avatar_path)

            try:
                img = Image.open(image_file)
            except Exception as e:
                flash(f'Ошибка при обработке изображения: {e}')
                return redirect(url_for('edit_profile'))

            target_size = min(current_app.config['MAX_IMAGE_SIZE'])

            width, height = img.size

            if width > height:
                new_height = target_size
                new_width = int(width * (target_size / height))
            else:
                new_width = target_size
                new_height = int(height * (target_size / width))
            
            img = img.resize((new_width, new_height), Image.LANCZOS)

            left = (new_width - target_size) / 2
            top = (new_height - target_size) / 2
            right = (new_width + target_size) / 2
            bottom = (new_height + target_size) / 2

            img = img.crop((left, top, right, bottom))

            final_avatar_filename = f"{base_filename}.png"
            final_avatar_path = os.path.join(avatar_dir, final_avatar_filename)

            img.save(final_avatar_path, optimize=True)

            flash('Ваш аватар успешно обновлен!')
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

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(Teacher).where(Teacher.username == username))
        if user is None:
            flash('Пользователь не найден.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('Вы не можете подписаться на самого себя.')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash(f'Вы подписались на {user.full_name}.')
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(Teacher).where(Teacher.username == username))
        if user is None:
            flash('Пользователь не найден.')
            return redirect(url_for('index'))
        if user == current_user:
            flash('Вы не можете отписаться от самого себя.')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user)
        db.session.commit()
        flash(f'Вы отписались от {user.full_name}.')
    return redirect(url_for('user', username=username))


@app.route('/explore', methods=['GET', 'POST'])
@login_required
def explore():
    form = SearchForm()
    if form.validate_on_submit():
        search = form.search.data
        grades = form.grades.data
        subjects = form.subjects.data
        worktypes = form.types_of_work.data
        return redirect(url_for('explore',
                                search=search,
                                subjects=','.join(subjects),
                                grades=','.join(grades),
                                worktypes=','.join(worktypes)))

    search = request.args.get('search', None)
    subjects = request.args.get('subjects', '').split(',')
    grades = request.args.get('grades', '').split(',')
    worktypes = request.args.get('worktypes', '').split(',')
    page = request.args.get('page', 1, type=int)

    form.search.data = search
    form.grades.data = grades
    form.subjects.data = subjects
    form.types_of_work.data = worktypes

    query = db.select(Page).order_by(Page.timestamp.desc())
    if search:
        search_term = f'%{search.lower()}%'
        query = query.filter(
            or_(
                func.lower(Page.name).like(search_term),
                func.lower(Page.description).like(search_term),
                func.lower(Teacher.full_name).like(search_term)
            )
        ).join(Page.author)
    if subjects and '' not in subjects:
        query = query.where(Page.subject.in_(subjects))
    if grades and '' not in grades:
        query = query.where(Page.grade.in_(grades))
    if worktypes and '' not in worktypes:
        query = query.where(Page.type_of_work.in_(worktypes))

    posts = db.paginate(query, page=page, per_page=app.config['POSTS_PER_PAGE'], error_out=False)
    next_url = url_for('explore', page=posts.next_num, search=search, subjects=','.join(subjects),
                       grades=','.join(grades), worktypes=','.join(worktypes)) \
        if posts.has_next else None
    prev_url = url_for('explore', page=posts.prev_num, search=search, subjects=','.join(subjects),
                       grades=','.join(grades), worktypes=','.join(worktypes)) \
        if posts.has_prev else None
    return render_template('explore.html', form=form, title='Поиск', posts=posts.items,
                           next_url=next_url, prev_url=prev_url, search=search, subjects=','.join(subjects),
                           grades=','.join(grades), worktypes=','.join(worktypes))


@app.route('/add_page', methods=['GET', 'POST'])
@login_required
def add_page():
    form = PageAddForm()
    if form.validate_on_submit():
        filename = None
        if form.file.data:
            file = form.file.data
            if file and allowed_file(file.filename):
                original_filename = file.filename
                filename = generate_unique_filename(original_filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
            else:
                flash('Недопустимый тип файла')
                return render_template('add_page.html', title='Добавление статьи', form=form)

        post = Page(name=form.name.data,
                    description=form.description.data,
                    grade=form.grade.data,
                    type_of_work=form.type_of_work.data,
                    subject=form.subject.data,
                    author=current_user,
                    link=filename,
                    original_filename=original_filename)
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
    page = db.first_or_404(sa.select(Page).where(Page.id == id))
    if page.author != current_user:
        abort(403)
    form = EditPageForm()
    if form.validate_on_submit():
        if form.file.data:
            uploaded_file = form.file.data
            if uploaded_file and allowed_file(uploaded_file.filename):
                new_filename = generate_unique_filename(uploaded_file.filename)
                new_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)

                try:
                    uploaded_file.save(new_filepath)

                    if page.link:
                        old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], page.link)
                        if os.path.exists(old_filepath):
                            os.remove(old_filepath)
                            flash(f'Старый файл "{page.original_filename}" удален.')
                        else:
                            flash(f'Предупреждение: старый файл "{page.original_filename}" не найден для удаления.')

                    page.link = new_filename
                    page.original_filename = uploaded_file.filename
                    flash('Файл успешно обновлен.')

                except Exception as e:
                    flash(f'Ошибка при сохранении файла: {e}')
                    return render_template('edit_page.html', title='Редактирование статьи', form=form)
            else:
                flash('Недопустимый тип файла для загрузки.')
                return render_template('edit_page.html', title='Редактирование статьи', form=form)

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


@app.route('/delete_page/<id>')
@login_required
def delete_page(id):
    page = db.first_or_404(sa.select(Page).where(Page.id == id))
    if page.author != current_user:
        abort(403)
    os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], page.link))
    db.session.delete(page)
    db.session.commit()
    flash('Статья удалена.')
    return redirect(url_for('index'))


@app.route('/download/<filename>')
@login_required
def download_file(filename):
    page = db.first_or_404(sa.select(Page).where(Page.link == filename))
    directory = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(directory, filename, as_attachment=True, download_name=page.original_filename)


@app.route('/privacy_policy')
def privacy_policy():
    return render_template('privacy_policy.html', title='Политика конфиденциальности')


@app.route('/faq')
def faq():
    return render_template('faq.html', title='FAQ')


@app.route('/about_us')
def about_us():
    return render_template('about_us.html', title='О нас')


@app.route('/avatars/<path:filename>')
def uploaded_avatar(filename):
    return send_from_directory(os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars'), filename)
