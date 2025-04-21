from datetime import datetime, timezone
from time import time
from typing import Optional
import jwt
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import ForeignKey
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from hashlib import md5

from app import db, login, app


@login.user_loader
def load_user(id):
    return db.session.get(Teacher, int(id))


teacher_subject = sa.Table(
    'teacher_subject', db.Model.metadata,
    sa.Column('id', sa.Integer, primary_key=True),
    sa.Column('teacher_id', sa.Integer, sa.ForeignKey('teachers.id'), primary_key=True),
    sa.Column('subject_id', sa.Integer, sa.ForeignKey('subjects.id'), primary_key=True)
)


class Subject(db.Model):
    __tablename__ = 'subjects'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(128))

    teachers: so.Mapped[list['Teacher']] = so.relationship('Teacher', secondary=teacher_subject,
                                                           back_populates='subjects')
    pages: so.Mapped[list['Page']] = so.relationship(back_populates='sub')

    def __repr__(self):
        return '<Subject {}>'.format(self.name)


class Region(db.Model):
    __tablename__ = 'regions'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(32), index=True, unique=True)

    settlements: so.Mapped[list['Settlement']] = so.relationship(back_populates='region')

    def __repr__(self):
        return 'Region {}'.format(self.name)


class Settlement(db.Model):
    __tablename__ = 'settlements'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(32), index=True, unique=True)
    region_id: so.Mapped[int] = so.mapped_column(ForeignKey('regions.id'))

    region: so.Mapped['Region'] = so.relationship(back_populates='settlements')

    def __repr__(self):
        return 'Settlement {}'.format(self.name)


class EducationalInstitution(db.Model):
    __tablename__ = 'educational_institutions'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True, unique=True)
    settlement_id: so.Mapped[str] = so.mapped_column(ForeignKey('settlements.id'))

    def __repr__(self):
        return 'EducationalInstitution {}'.format(self.name)


class Teacher(UserMixin, db.Model):
    __tablename__ = 'teachers'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    full_name: so.Mapped[str] = so.mapped_column(sa.String(64))
    about: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    educational_institution: so.Mapped[int] = so.mapped_column(sa.ForeignKey(EducationalInstitution.id), index=True)

    subjects: so.Mapped[list['Subject']] = so.relationship('Subject', secondary=teacher_subject,
                                                           back_populates='teachers')
    pages: so.WriteOnlyMapped['Page'] = so.relationship(back_populates='author')
    reviews: so.Mapped[list['Review']] = so.relationship(back_populates='author')

    def __repr__(self):
        return '<Teacher {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return f'https://www.gravatar.com/avatar/{digest}?d=identicon&s={size}'

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return db.session.get(Teacher, id)


class TypeOfWork(db.Model):
    __tablename__ = 'types_of_work'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)

    pages: so.Mapped[list['Page']] = so.relationship(back_populates='tow')


class Grade(db.Model):
    __tablename__ = 'grades'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(8), index=True, unique=True)

    pages: so.Mapped[list['Page']] = so.relationship(back_populates='grd')


class Page(db.Model):
    __tablename__ = 'pages'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(128), index=True)
    description: so.Mapped[Optional[str]] = so.mapped_column(sa.String(512))
    teacher_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Teacher.id), index=True)
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    link: so.Mapped[Optional[str]] = so.mapped_column(sa.String(64))
    average_rating: so.Mapped[float] = so.mapped_column(sa.Float(1), default=0)
    grade: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Grade.id), index=True)
    type_of_work: so.Mapped[int] = so.mapped_column(sa.ForeignKey(TypeOfWork.id), index=True)
    subject: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Subject.id), index=True)

    reviews: so.Mapped[list['Review']] = so.relationship(back_populates='page')
    author: so.Mapped['Teacher'] = so.relationship(back_populates='pages')
    tow: so.Mapped['TypeOfWork'] = so.relationship(back_populates='pages')
    sub: so.Mapped['Subject'] = so.relationship(back_populates='pages')
    grd: so.Mapped['Grade'] = so.relationship(back_populates='pages')

    def __repr__(self):
        return '<Page {}>'.format(self.description)


class Review(db.Model):
    __tablename__ = 'reviews'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    rate: so.Mapped[int] = so.mapped_column()
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    comment: so.Mapped[str] = so.mapped_column(sa.String(256))
    author_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Teacher.id), index=True)
    page_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Page.id), index=True)

    author: so.Mapped['Teacher'] = so.relationship(back_populates='reviews')
    page: so.Mapped['Page'] = so.relationship(back_populates='reviews')

    def __repr__(self):
        return '<Review [Rate={}] {}>'.format(self.rate, self.comment)
