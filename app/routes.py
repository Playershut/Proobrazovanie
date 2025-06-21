import os
import uuid
from urllib.parse import urlsplit

import sqlalchemy as sa
from PIL import Image
from app import app, db
from app.email import send_password_reset_email
from app.forms import (
    LoginForm, RegistrationForm, EditProfileForm, PageAddForm, ReviewAddForm,
    EditPageForm, ResetPasswordRequestForm, ResetPasswordForm, SearchForm, EmptyForm
)
from app.models import User, Subject, Page, Review, Notification, Region, Settlement, \
    EducationalInstitution
from flask import jsonify
from flask import render_template, flash, redirect, url_for, request, current_app, abort, \
    send_from_directory, Response, Blueprint
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import or_, func
from sqlalchemy.sql import text
from werkzeug.utils import secure_filename


# --- Вспомогательные функции ---

def allowed_file(filename):
    """
    Проверяет, разрешен ли тип файла для загрузки.
    """
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def generate_unique_filename(filename):
    """
    Генерирует уникальное имя файла с сохранением его расширения.
    """
    _, ext = os.path.splitext(filename)
    return uuid.uuid4().hex + ext


# --- Роуты приложения ---

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    """
    Домашняя страница, отображает последние статьи.
    """
    page_num = request.args.get('page', 1, type=int)
    query = sa.select(Page).order_by(Page.timestamp.desc())
    posts = db.paginate(query, page=page_num, per_page=app.config['POSTS_PER_PAGE'],
                        error_out=False)

    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None

    return render_template(
        'index.html',
        title='Домашняя страница',
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Страница входа пользователя.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()
    if form.validate_on_submit():
        user_obj = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user_obj is None or not user_obj.check_password(form.password.data):
            flash('Неверный логин или пароль')
            return redirect(url_for('login'))

        login_user(user_obj, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Вход', form=form)


@app.route('/logout')
def logout():
    """
    Выход пользователя из системы.
    """
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    Страница регистрации нового пользователя.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user_obj = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            about=form.about.data,
            educational_institution=form.educational_institution.data
        )
        user_obj.set_password(form.password.data)
        user_obj.subjects = db.session.scalars(
            sa.select(Subject).where(Subject.id.in_(form.subjects.data))
        ).all()
        db.session.add(user_obj)
        db.session.commit()
        flash('Поздравляем, теперь Вы зарегистрированный пользователь!')
        return redirect(url_for('index'))
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    """
    Профиль пользователя, отображает его статьи.
    """
    user_obj = db.first_or_404(sa.select(User).where(User.username == username))
    page_num = request.args.get('page', 1, type=int)
    query = user_obj.pages.select().order_by(Page.timestamp.desc())
    posts = db.paginate(query, page=page_num,
                        per_page=app.config['POSTS_PER_PAGE'],
                        error_out=False)

    next_url = url_for('user', username=user_obj.username,
                       page=posts.next_num) if posts.has_next else None
    prev_url = url_for('user', username=user_obj.username,
                       page=posts.prev_num) if posts.has_prev else None

    form = EmptyForm()

    return render_template(
        'user.html',
        user=user_obj,
        title=f'Профиль {username}',
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
        form=form,
        followed=user_obj.followed.all()
    )


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    Редактирование профиля пользователя.
    """
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        if form.avatar.data:
            image_file = form.avatar.data

            allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
            file_extension = image_file.filename.rsplit('.', 1)[1].lower()
            if file_extension not in allowed_extensions:
                flash('Разрешены только изображения в форматах PNG, JPG, JPEG, GIF.')
                return redirect(url_for('edit_profile'))

            avatar_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
            os.makedirs(avatar_dir, exist_ok=True)

            base_filename = current_user.username

            for ext in current_app.config['ALLOWED_EXTENSIONS_IMAGES']:
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
        current_user.subjects = db.session.scalars(
            sa.select(Subject).where(Subject.id.in_(form.subjects.data))
        ).all()
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
    """
    Подписаться на другого пользователя.
    """
    form = EmptyForm()
    if form.validate_on_submit():
        user_to_follow = db.session.scalar(sa.select(User).where(User.username == username))
        if user_to_follow is None:
            flash('Пользователь не найден.')
            return redirect(url_for('index'))
        if user_to_follow == current_user:
            flash('Вы не можете подписаться на самого себя.')
            return redirect(url_for('user', username=username))
        current_user.follow(user_to_follow)
        db.session.commit()
        flash(f'Вы подписались на {user_to_follow.full_name}.')
    return redirect(url_for('user', username=username))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    """
    Отписаться от другого пользователя.
    """
    form = EmptyForm()
    if form.validate_on_submit():
        user_to_unfollow = db.session.scalar(sa.select(User).where(User.username == username))
        if user_to_unfollow is None:
            flash('Пользователь не найден.')
            return redirect(url_for('index'))
        if user_to_unfollow == current_user:
            flash('Вы не можете отписаться от самого себя.')
            return redirect(url_for('user', username=username))
        current_user.unfollow(user_to_unfollow)
        db.session.commit()
        flash(f'Вы отписались от {user_to_unfollow.full_name}.')
    return redirect(url_for('user', username=username))


@app.route('/explore', methods=['GET', 'POST'])
@login_required
def explore():
    """
    Страница исследования/поиска статей с фильтрами.
    """
    form = SearchForm()
    if form.validate_on_submit():
        search_term = form.search.data
        grades_selected = form.grades.data
        subjects_selected = form.subjects.data
        worktypes_selected = form.types_of_work.data
        return redirect(url_for(
            'explore',
            search=search_term,
            subjects=','.join(subjects_selected),
            grades=','.join(grades_selected),
            worktypes=','.join(worktypes_selected)
        ))

    search_term = request.args.get('search', None)
    subjects_param = request.args.get('subjects', '').split(',')
    grades_param = request.args.get('grades', '').split(',')
    worktypes_param = request.args.get('worktypes', '').split(',')
    page_num = request.args.get('page', 1, type=int)

    form.search.data = search_term
    form.grades.data = grades_param
    form.subjects.data = subjects_param
    form.types_of_work.data = worktypes_param

    query = db.select(Page).order_by(Page.timestamp.desc())

    if search_term:
        search_like = f'%{search_term.lower()}%'
        query = query.filter(
            or_(
                func.lower(Page.name).like(search_like),
                func.lower(Page.description).like(search_like),
                func.lower(User.full_name).like(search_like)
            )
        ).join(Page.author)

    if subjects_param and '' not in subjects_param:
        query = query.where(Page.subject.in_(subjects_param))
    if grades_param and '' not in grades_param:
        query = query.where(Page.grade.in_(grades_param))
    if worktypes_param and '' not in worktypes_param:
        query = query.where(Page.type_of_work.in_(worktypes_param))

    posts = db.paginate(query, page=page_num, per_page=app.config['POSTS_PER_PAGE'], error_out=False)

    def get_explore_url(page_number):
        return url_for(
            'explore',
            page=page_number,
            search=search_term,
            subjects=','.join(subjects_param),
            grades=','.join(grades_param),
            worktypes=','.join(worktypes_param)
        )

    next_url = get_explore_url(posts.next_num) if posts.has_next else None
    prev_url = get_explore_url(posts.prev_num) if posts.has_prev else None

    return render_template(
        'explore.html',
        form=form,
        title='Поиск',
        posts=posts.items,
        next_url=next_url,
        prev_url=prev_url,
        search=search_term,
        subjects=','.join(subjects_param),
        grades=','.join(grades_param),
        worktypes=','.join(worktypes_param)
    )


@app.route('/add_page', methods=['GET', 'POST'])
@login_required
def add_page():
    """
    Добавление новой статьи/материала.
    """
    form = PageAddForm()
    if form.validate_on_submit():
        filename = None
        original_filename = None

        if form.file.data:
            file = form.file.data
            if file and allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                filename = generate_unique_filename(original_filename)
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                try:
                    file.save(filepath)
                except Exception as e:
                    flash(f'Ошибка при сохранении файла: {e}')
                    return render_template('add_page.html', title='Добавление статьи', form=form)
            else:
                flash('Недопустимый тип файла.')
                return render_template('add_page.html', title='Добавление статьи', form=form)

        post = Page(
            name=form.name.data,
            description=form.description.data,
            grade=form.grade.data,
            type_of_work=form.type_of_work.data,
            subject=form.subject.data,
            author=current_user,
            link=filename,
            original_filename=original_filename
        )

        db.session.add(post)
        db.session.flush()

        followers_result = db.session.execute(
            text("SELECT follower_id FROM followers WHERE followed_id = :id"),
            {"id": current_user.id}
        ).fetchall()

        for follower_tuple in followers_result:
            follower_id = follower_tuple[0]
            notif = Notification(
                user_id=follower_id,
                message=f"Новая статья от {current_user.full_name or current_user.username}: {post.name}",
                link=url_for('page', id=post.id)
            )
            db.session.add(notif)

        db.session.commit()
        flash('Вы выложили статью!')
        return redirect(url_for('index'))

    return render_template('add_page.html', title='Добавление статьи', form=form)


@app.route('/page/<int:id>', methods=['GET', 'POST'])
@login_required
def page(id):
    """
    Отображение страницы со статьей и возможность добавления/удаления отзывов.
    """
    current_page = db.first_or_404(sa.select(Page).where(Page.id == id))
    form = ReviewAddForm()

    review_to_delete_id = request.args.get('delete', 0, type=int)
    if review_to_delete_id:
        review = db.session.get(Review, review_to_delete_id)
        if review and review.author == current_user and review.page == current_page:
            db.session.delete(review)
            db.session.commit()
            flash('Отзыв был удалён.')
            return redirect(url_for('page', id=current_page.id))

    reviews_adding_visibility = (
            current_page.author != current_user and
            all(r.author != current_user for r in current_page.reviews)
    )

    if form.validate_on_submit():
        if not reviews_adding_visibility:
            flash('Вы не можете добавить отзыв к этой статье.')
            return redirect(url_for('page', id=current_page.id))

        review = Review(
            rate=form.rate.data,
            comment=form.comment.data,
            author=current_user,
            page=current_page
        )
        db.session.add(review)
        db.session.commit()

        all_reviews = current_page.reviews
        if all_reviews:
            current_page.average_rating = sum(r.rate for r in all_reviews) / len(all_reviews)
        else:
            current_page.average_rating = 0.0
        db.session.commit()

        flash('Вы оставили отзыв!')
        return redirect(url_for('page', id=current_page.id))

    return render_template(
        'page.html',
        page=current_page,
        title=current_page.name,
        form=form,
        reviews=current_page.reviews,
        rav=reviews_adding_visibility
    )


@app.route('/edit_page/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_page(id):
    """
    Редактирование существующей статьи.
    """
    current_page = db.first_or_404(sa.select(Page).where(Page.id == id))
    if current_page.author != current_user:
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

                    if current_page.link:
                        old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                                    current_page.link)
                        if os.path.exists(old_filepath):
                            os.remove(old_filepath)
                            flash(f'Старый файл "{current_page.original_filename}" удален.')
                        else:
                            flash(
                                f'Предупреждение: старый файл "{current_page.original_filename}" не найден для удаления.')

                    current_page.link = new_filename
                    current_page.original_filename = uploaded_file.filename
                    flash('Файл успешно обновлен.')

                except Exception as e:
                    flash(f'Ошибка при сохранении файла: {e}')
                    return render_template('edit_page.html', title='Редактирование статьи', form=form)
            else:
                flash('Недопустимый тип файла для загрузки.')
                return render_template('edit_page.html', title='Редактирование статьи', form=form)

        current_page.name = form.name.data
        current_page.description = form.description.data
        current_page.grade = form.grade.data
        current_page.type_of_work = form.type_of_work.data
        current_page.subject = form.subject.data
        db.session.commit()
        flash('Ваши изменения сохранены.')
        return redirect(url_for('edit_page', id=current_page.id))
    elif request.method == 'GET':
        form.name.data = current_page.name
        form.description.data = current_page.description
        form.grade.data = str(current_page.grade)
        form.type_of_work.data = str(current_page.type_of_work)
        form.subject.data = str(current_page.subject)
    return render_template('edit_page.html', title='Редактирование статьи', form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """
    Запрос на сброс пароля по электронной почте.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user_obj = db.session.scalar(
            sa.select(User).where(User.email == form.email.data)
        )
        if user_obj:
            send_password_reset_email(user_obj)
        flash('Проверьте Вашу электронную почту для инструкций по сбросу пароля.')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Сброс пароля', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Сброс пароля по токену из письма.
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user_obj = User.verify_reset_password_token(token)
    if not user_obj:
        flash('Ссылка для сброса пароля недействительна или устарела.')
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user_obj.set_password(form.password.data)
        db.session.commit()
        flash('Ваш пароль был сброшен.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/delete_page/<int:id>')
@login_required
def delete_page(id):
    """
    Удаление статьи. Только автор может удалить свою статью.
    """
    current_page = db.first_or_404(sa.select(Page).where(Page.id == id))
    if current_page.author != current_user:
        abort(403)

    if current_page.link:
        filepath_to_delete = os.path.join(current_app.config['UPLOAD_FOLDER'], current_page.link)
        if os.path.exists(filepath_to_delete):
            os.remove(filepath_to_delete)
            flash(f'Связанный файл "{current_page.original_filename}" удален.')
        else:
            flash(f'Предупреждение: файл "{current_page.original_filename}" не найден для удаления.')

    db.session.delete(current_page)
    db.session.commit()
    flash('Статья удалена.')
    return redirect(url_for('index'))


@app.route('/download/<filename>')
@login_required
def download_file(filename):
    """
    Скачивание загруженных файлов.
    """
    page_with_file = db.first_or_404(sa.select(Page).where(Page.link == filename))
    directory = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(directory, filename, as_attachment=True,
                               download_name=page_with_file.original_filename)


@app.route('/privacy_policy')
def privacy_policy():
    """
    Страница политики конфиденциальности.
    """
    return render_template('privacy_policy.html', title='Политика конфиденциальности')


@app.route('/faq')
def faq():
    """
    Страница часто задаваемых вопросов.
    """
    return render_template('faq.html', title='FAQ')


@app.route('/about_us')
def about_us():
    """
    Страница "О нас".
    """
    return render_template('about_us.html', title='О нас')


@app.route('/avatars/<path:filename>')
def uploaded_avatar(filename):
    """
    Обслуживание загруженных аватаров пользователей.
    """
    avatar_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
    full_path = os.path.join(avatar_dir, filename)
    if not os.path.exists(full_path):
        return "Avatar not found", 404

    try:
        with open(full_path, 'rb') as f:
            image_data = f.read()

        if filename.lower().endswith('.png'):
            mimetype = 'image/png'
        elif filename.lower().endswith(('.jpg', '.jpeg')):
            mimetype = 'image/jpeg'
        elif filename.lower().endswith('.gif'):
            mimetype = 'image/gif'
        else:
            mimetype = 'application/octet-stream'

        return Response(image_data, mimetype=mimetype)
    except Exception as e:
        return "Internal server error serving avatar", 500


# --- API-эндпоинты для динамических полей ---

@app.route('/api/settlements_by_region/<int:region_id>')
def get_settlements_by_region(region_id):
    """
    Возвращает список населенных пунктов для заданного региона.
    """
    settlements = db.session.execute(
        sa.select(Settlement).where(Settlement.region_id == region_id)
        .order_by(Settlement.name)
    ).scalars().all()
    settlement_list = [{'id': s.id, 'name': s.name} for s in settlements]
    return jsonify(settlement_list)


@app.route('/api/institutions_by_settlement/<int:settlement_id>')
def get_institutions_by_settlement(settlement_id):
    """
    Возвращает список учебных заведений для заданного населенного пункта.
    """
    institutions = db.session.execute(
        sa.select(EducationalInstitution).where(EducationalInstitution.settlement_id == settlement_id)
        .order_by(EducationalInstitution.name)
    ).scalars().all()
    institution_list = [{'id': i.id, 'name': i.name} for i in institutions]
    return jsonify(institution_list)
