import os
from datetime import datetime, timezone
from time import time
from typing import Optional, List

import jwt
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask import current_app, url_for
from flask_login import UserMixin
from hashlib import md5
from sqlalchemy import ForeignKey, Table, Column, Integer, String, Text, Boolean, DateTime, Float
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login, app


# Загрузчик пользователя для Flask-Login
@login.user_loader
def load_user(id):
    """
    Загружает пользователя по его ID для Flask-Login.
    """
    return db.session.get(User, int(id))


# Вспомогательные таблицы для связей многие-ко-многим
followers = Table(
    'followers', db.Model.metadata,
    Column('follower_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('followed_id', Integer, ForeignKey('users.id'), primary_key=True)
)

teacher_subject = Table(
    'teacher_subject', db.Model.metadata,
    Column('teacher_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('subject_id', Integer, ForeignKey('subjects.id'), primary_key=True)
)


# === СЛОВАРИ ===

# Модель Предмета
class Subject(db.Model):
    """
    Модель для представления учебных предметов.
    """
    __tablename__ = 'subjects'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(String(128))

    teachers: so.Mapped[List['User']] = so.relationship(
        'Teacher', secondary=teacher_subject, back_populates='subjects'
    )
    courses: so.WriteOnlyMapped[List['Course']] = so.relationship(back_populates='subject', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Subject {self.name}>'


# Модель Региона
class Region(db.Model):
    """
    Модель для представления регионов.
    """
    __tablename__ = 'regions'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(String(32), index=True, unique=True)

    settlements: so.Mapped[List['Settlement']] = so.relationship(back_populates='region')

    def __repr__(self):
        return f'<Region {self.name}>'


# Модель Населенного пункта
class Settlement(db.Model):
    """
    Модель для представления населенных пунктов.
    """
    __tablename__ = 'settlements'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(String(32), index=True, unique=True)
    region_id: so.Mapped[int] = so.mapped_column(ForeignKey('regions.id'))

    region: so.Mapped['Region'] = so.relationship(back_populates='settlements')

    def __repr__(self):
        return f'<Settlement {self.name}>'


# Модель Учебного заведения
class EducationalInstitution(db.Model):
    """
    Модель для представления учебных заведений.
    """
    __tablename__ = 'educational_institutions'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(String(128), index=True, unique=True)
    settlement_id: so.Mapped[int] = so.mapped_column(ForeignKey('settlements.id'))

    users: so.WriteOnlyMapped[List['User']] = so.relationship(back_populates='educational_institution', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<EducationalInstitution {self.name}>'


# Модель Типа работы
class TypeOfWork(db.Model):
    """
    Модель для представления типов учебных работ (например, "Конспект", "Презентация").
    """
    __tablename__ = 'types_of_work'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(String(64), index=True, unique=True)

    pages: so.Mapped[List['Page']] = so.relationship(back_populates='tow')

    def __repr__(self):
        return f'<TypeOfWork {self.name}>'


# Модель Класса/Грейда
class Grade(db.Model):
    """
    Модель для представления классов/грейдов (например, "5 класс", "11 класс").
    """
    __tablename__ = 'grades'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(String(8), index=True, unique=True)

    courses: so.WriteOnlyMapped[List['Course']] = so.relationship(back_populates='grade', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Grade {self.name}>'


# Модель Ролей
class Role(db.Model):
    __tablename__ = 'roles'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(String(16), index=True, unique=True)

    def __repr__(self):
        return f'<Role {self.name}>'


# === ТАБЛИЦЫ ===

# Модель Уведомления
class Notification(db.Model):
    """
    Модель для хранения уведомлений пользователей.
    """
    __tablename__ = 'notifications'

    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(ForeignKey('users.id'), nullable=False)
    message: so.Mapped[str] = so.mapped_column(Text, nullable=False)
    link: so.Mapped[Optional[str]] = so.mapped_column(String(256))
    is_read: so.Mapped[bool] = so.mapped_column(Boolean, default=False)
    timestamp: so.Mapped[datetime] = so.mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    user: so.Mapped['User'] = so.relationship(back_populates='notifications')

    def __repr__(self):
        return f'<Notification {self.id}: {self.message[:50]}>'


# Модель Курса
class Course(db.Model):
    """
    Модель для представления учебных курсов.
    """
    __tablename__ = 'courses'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    title: so.Mapped[str] = so.mapped_column(String(128), nullable=False)
    description: so.Mapped[Optional[str]] = so.mapped_column(Text)
    # start_date: so.Mapped[datetime] = so.mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    # end_date: so.Mapped[Optional[datetime]] = so.mapped_column(DateTime)

    teacher_id: so.Mapped[int] = so.mapped_column(ForeignKey('users.id'), nullable=False)
    teacher: so.Mapped['User'] = so.relationship(back_populates='courses_taught')

    subject_id: so.Mapped[int] = so.mapped_column(ForeignKey('subjects.id'), nullable=False)
    subject: so.Mapped['Subject'] = so.relationship(back_populates='courses')

    grade_id: so.Mapped[int] = so.mapped_column(ForeignKey('grades.id'), nullable=False)
    grade: so.Mapped['Grade'] = so.relationship(back_populates='courses')

    pages: so.WriteOnlyMapped[List['Page']] = so.relationship(back_populates='course', cascade="all, delete-orphan")
    assignments: so.WriteOnlyMapped[List['Assignment']] = so.relationship(back_populates='course', cascade="all, delete-orphan")
    enrollments: so.WriteOnlyMapped[List['CourseEnrollment']] = so.relationship(back_populates='course', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Course {self.title}>'


# Модель Зачисления на Курс
class CourseEnrollment(db.Model):
    """
    Модель для зачисления пользователей на курсы.
    Включает роль пользователя в рамках этого курса.
    """
    __tablename__ = 'course_enrollments'
    user_id: so.Mapped[int] = so.mapped_column(ForeignKey('users.id'), primary_key=True)
    course_id: so.Mapped[int] = so.mapped_column(ForeignKey('courses.id'), primary_key=True)
    enrollment_date: so.Mapped[datetime] = so.mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    # Роль пользователя ВНУТРИ ЭТОГО КУРСА
    role_id: so.Mapped[int] = so.mapped_column(Integer, default=1, nullable=False)
    role: so.Mapped['Role'] = so.relationship(back_populates='enrollments')

    user: so.Mapped['User'] = so.relationship(back_populates='enrollments')
    course: so.Mapped['Course'] = so.relationship(back_populates='enrollments')

    def __repr__(self):
        return f'<Enrollment User:{self.user_id} Course:{self.course_id} Role:{self.role_in_course}>'


# Модель Задания
class Assignment(db.Model):
    """
    Модель для представления заданий в курсе.
    """
    __tablename__ = 'assignments'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    course_id: so.Mapped[int] = so.mapped_column(ForeignKey('courses.id'), nullable=False)
    title: so.Mapped[str] = so.mapped_column(String(128), nullable=False)
    description: so.Mapped[Optional[str]] = so.mapped_column(Text)
    due_date: so.Mapped[datetime] = so.mapped_column(DateTime, nullable=False)

    course: so.Mapped['Course'] = so.relationship(back_populates='assignments')
    submissions: so.WriteOnlyMapped[List['Submission']] = so.relationship(back_populates='assignment', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Assignment {self.title} (Course:{self.course_id})>'


# Модель Сдачи задания
class Submission(db.Model):
    """
    Модель для хранения сданных студентами работ по заданиям.
    """
    __tablename__ = 'submissions'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    assignment_id: so.Mapped[int] = so.mapped_column(ForeignKey('assignments.id'), nullable=False)
    student_id: so.Mapped[int] = so.mapped_column(ForeignKey('users.id'), nullable=False)
    submission_date: so.Mapped[datetime] = so.mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    file_link: so.Mapped[Optional[str]] = so.mapped_column(String(256))
    text_submission: so.Mapped[Optional[str]] = so.mapped_column(Text)
    grade: so.Mapped[Optional[float]] = so.mapped_column(Float)
    feedback: so.Mapped[Optional[str]] = so.mapped_column(Text)

    assignment: so.Mapped['Assignment'] = so.relationship(back_populates='submissions')
    student: so.Mapped['User'] = so.relationship(back_populates='submissions')

    def __repr__(self):
        return f'<Submission {self.id} for Assignment:{self.assignment_id} by User:{self.student_id}>'


# Модель Пользователя (Бывшая Teacher)
class User(UserMixin, db.Model):
    """
    Модель для представления пользователей системы (учителей, студентов, администраторов).
    """
    __tablename__ = 'users'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(String(256))
    full_name: so.Mapped[str] = so.mapped_column(String(64))
    about: so.Mapped[Optional[str]] = so.mapped_column(String(256))
    educational_institution_id: so.Mapped[int] = so.mapped_column(
        ForeignKey('educational_institutions.id'),
        index=True, nullable=True)

    # Связь с моделью Role
    role_id: so.Mapped[int] = so.mapped_column(ForeignKey('roles.id'), nullable=False)
    role: so.Mapped['Role'] = so.relationship(back_populates='users')

    # Образовательное учреждение
    educational_institution: so.Mapped['EducationalInstitution'] = so.relationship(
        back_populates='users')

    followed: so.Mapped[List['User']] = so.relationship(
        'User',
        secondary=followers,
        primaryjoin=followers.c.follower_id == id,
        secondaryjoin=followers.c.followed_id == id,
        backref=so.backref('followers', lazy='dynamic'),
        lazy='dynamic'
    )

    # Список курсов, которые пользователь преподает (для учителей)
    courses_taught: so.WriteOnlyMapped[List['Course']] = so.relationship('Course', back_populates='teacher')
    # Зачисления пользователя на курсы (для студентов и учителей)
    enrollments: so.WriteOnlyMapped[List['CourseEnrollment']] = so.relationship('CourseEnrollment', back_populates='user', cascade="all, delete-orphan")
    # Сданные работы пользователя
    submissions: so.WriteOnlyMapped[List['Submission']] = so.relationship('Submission', back_populates='student', cascade="all, delete-orphan")

    pages: so.WriteOnlyMapped['Page'] = so.relationship(back_populates='author', cascade="all, delete-orphan")
    reviews: so.Mapped[List['Review']] = so.relationship(back_populates='author', cascade="all, delete-orphan")
    notifications: so.WriteOnlyMapped['Notification'] = so.relationship(back_populates='user', cascade="all, delete-orphan")
    subjects: so.Mapped[List['Subject']] = so.relationship('Subject', secondary=teacher_subject, back_populates='teachers')

    def set_password(self, password):
        """Устанавливает хэш пароля для пользователя."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверяет введенный пароль с хэшем."""
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        """
        Возвращает URL аватара пользователя.
        Сначала пытается найти загруженный аватар, затем использует Gravatar.
        """
        possible_extensions = ['.png', '.jpg', '.jpeg', '.gif']
        base_filename = self.username
        avatar_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')

        for ext in possible_extensions:
            full_filename = base_filename + ext
            avatar_path = os.path.join(avatar_dir, full_filename)

            if os.path.exists(avatar_path):
                return url_for('uploaded_avatar', filename=full_filename, _external=True)

        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def follow(self, user):
        """Подписывается на другого учителя."""
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        """Отписывается от другого учителя."""
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        """Проверяет, подписан ли текущий пользователь на другого учителя."""
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def get_reset_password_token(self, expires_in=600):
        """Генерирует токен для сброса пароля."""
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256'
        )

    @staticmethod
    def verify_reset_password_token(token):
        """Проверяет токен сброса пароля и возвращает пользователя."""
        try:
            user_id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except Exception:
            return None
        return db.session.get(User, user_id)

    def is_student(self):
        return self.role.name == 'student'

    def is_teacher(self):
        return self.role.name == 'teacher'

    def is_admin(self):
        return self.role.name == 'admin'

    def __repr__(self):
        return f'<User {self.username} ({self.role.name})>'


# Модель Страницы/Статьи
class Page(db.Model):
    """
    Модель для представления учебных материалов/статей, загруженных учителями.
    """
    __tablename__ = 'pages'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(String(128), index=True)
    description: so.Mapped[Optional[str]] = so.mapped_column(String(512))
    teacher_id: so.Mapped[int] = so.mapped_column(ForeignKey(User.id), index=True)
    timestamp: so.Mapped[datetime] = so.mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    link: so.Mapped[Optional[str]] = so.mapped_column(String(256))
    original_filename: so.Mapped[Optional[str]] = so.mapped_column(String(256))
    average_rating: so.Mapped[float] = so.mapped_column(Float(1), default=0)
    course_id: so.Mapped[int] = so.mapped_column(ForeignKey('courses.id'), index=True, nullable=False)
    type_of_work: so.Mapped[int] = so.mapped_column(ForeignKey(TypeOfWork.id), index=True)

    reviews: so.Mapped[List['Review']] = so.relationship(back_populates='page', cascade="all, delete-orphan")
    author: so.Mapped['User'] = so.relationship(back_populates='pages')
    tow: so.Mapped['TypeOfWork'] = so.relationship(back_populates='pages')
    course: so.Mapped['Course'] = so.relationship(back_populates='pages')

    def __repr__(self):
        return f'<Page {self.name} (Course:{self.course_id})>'


# Модель Отзыва
class Review(db.Model):
    """
    Модель для хранения отзывов о статьях.
    """
    __tablename__ = 'reviews'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    rate: so.Mapped[int] = so.mapped_column(Integer)
    timestamp: so.Mapped[datetime] = so.mapped_column(DateTime, index=True, default=lambda: datetime.now(timezone.utc))
    comment: so.Mapped[str] = so.mapped_column(String(256))
    author_id: so.Mapped[int] = so.mapped_column(ForeignKey(User.id), index=True)
    page_id: so.Mapped[int] = so.mapped_column(ForeignKey(Page.id), index=True)

    author: so.Mapped['User'] = so.relationship(back_populates='reviews')
    page: so.Mapped['Page'] = so.relationship(back_populates='reviews')

    def __repr__(self):
        return f'<Review [Rate={self.rate}] {self.comment[:50]}>'
