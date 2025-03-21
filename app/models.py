from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import JSON

from app import db


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    full_name: so.Mapped[str] = so.mapped_column(sa.String(64))
    about: so.Mapped[str] = so.mapped_column(sa.String(256))
    subjects: so.Mapped[sa.JSON] = so.mapped_column(sa.JSON)
    educational_institutions: so.Mapped[sa.JSON] = so.mapped_column(sa.JSON)

    pages: so.WriteOnlyMapped['Page'] = so.relationship(back_populates='author')

    def __repr__(self):
        return '<Teacher {}>'.format(self.username)


class Page(db.Model):
    __tablename__ = 'pages'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    description: so.Mapped[str] = so.mapped_column(sa.String(256))
    teacher_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Teacher.id), index=True)
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    link: so.Mapped[str] = so.mapped_column(sa.String(64))
    average_rating: so.Mapped[float] = so.mapped_column(sa.Float(1))
    categories: so.Mapped[JSON] = so.mapped_column(sa.JSON)
    reviews: so.Mapped[sa.JSON] = so.mapped_column(sa.JSON)

    author: so.Mapped[Teacher] = so.relationship(back_populates='pages')

    def __repr__(self):
        return '<Page {}>'.format(self.description)
