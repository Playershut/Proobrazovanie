import sqlalchemy as sa
from flask import current_app
from flask_login import current_user
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.fields.choices import SelectMultipleField
from wtforms.fields.simple import TextAreaField, FileField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length

from app import db
from app.models import Teacher, Subject, EducationalInstitution, Grade, TypeOfWork, Settlement


class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired('Для входа требуется логин')])
    password = PasswordField('Пароль', validators=[DataRequired('Для входа требуется пароль')])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Вход')


class RegistrationForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    email = StringField('Почта', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField(
        'Повтор пароля', validators=[DataRequired(), EqualTo('password')])
    full_name = StringField('ФИО', validators=[DataRequired()])
    about = TextAreaField('О себе', validators=[Length(max=256)])
    subjects = SelectMultipleField('Преподаваемые предметы', validators=[DataRequired()], choices=[])
    settlement = SelectField('Населённый пункт', validators=[DataRequired()], choices=[],
                             render_kw={'class': 'searchable-select'})
    educational_institution = SelectField('Учебное заведение', validators=[DataRequired()], choices=[],
                                          render_kw={'class': 'searchable-select'})
    submit = SubmitField('Зарегистрироваться')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)

        self.subjects.choices = [(sub.id, sub.name) for sub in Subject.query.all()]
        self.settlement.choices = [(s.id, s.name) for s in Settlement.query.all()]
        self.educational_institution.choices = [(ei.id, ei.name) for ei in EducationalInstitution.query.all()]

    def validate_username(self, username):
        user = db.session.scalar(sa.select(Teacher).where(Teacher.username == username.data))
        if user is not None:
            raise ValidationError('Пожалуйста, используйте другой логин')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(Teacher).where(Teacher.email == email.data))
        if user is not None:
            raise ValidationError('Пожалуйста, используйте другой почтовый адрес')


class EditProfileForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired()])
    full_name = StringField('ФИО', validators=[DataRequired()])
    avatar = FileField('Изменить аватар', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'])])
    about = TextAreaField('О себе', validators=[Length(max=256)])
    subjects = SelectMultipleField('Преподаваемые предметы', validators=[DataRequired()], choices=[])
    educational_institution = SelectField('Учебное заведение', validators=[DataRequired()], choices=[],
                                          render_kw={'class': 'searchable-select'})
    submit = SubmitField('Подтвердить')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username
        self.subjects.choices = [(s.id, s.name) for s in Subject.query.all()]
        self.educational_institution.choices = [(ei.id, ei.name) for ei in EducationalInstitution.query.all()]

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(Teacher).where(Teacher.username == self.username.data))
            if user is not None:
                raise ValidationError('Пожалуйста, используйте другоой логин')


class PageAddForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired(), Length(min=1, max=128)])
    description = TextAreaField('Описание', validators=[Length(max=512)])
    grade = SelectField('Класс/курс', validators=[DataRequired()], choices=[])
    type_of_work = SelectField('Тип работы', validators=[DataRequired()], choices=[])
    subject = SelectField('Предмет', validators=[DataRequired()], choices=[])
    file = FileField('Файл', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.grade.choices = [(g.id, g.name) for g in Grade.query.order_by(Grade.id).all()]
        self.type_of_work.choices = [(tow.id, tow.name) for tow in TypeOfWork.query.order_by(TypeOfWork.id).all()]
        self.subject.choices = [(s.id, s.name) for s in current_user.subjects]


class ReviewAddForm(FlaskForm):
    rate = SelectField('Оценка', validators=[DataRequired()], choices=[])
    comment = TextAreaField('Комментарий')
    submit = SubmitField('Оставить отзыв')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.rate.choices = [(i, i) for i in range(1, 6)]


class EditPageForm(FlaskForm):
    name = StringField('Название', validators=[DataRequired(), Length(min=1, max=128)])
    description = TextAreaField('Описание', validators=[Length(max=512)])
    grade = SelectField('Класс/курс', validators=[DataRequired()], choices=[])
    type_of_work = SelectField('Тип работы', validators=[DataRequired()], choices=[])
    subject = SelectField('Предмет', validators=[DataRequired()], choices=[])
    file = FileField('Файл', validators=[DataRequired()])
    submit = SubmitField('Подтвердить')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.grade.choices = [(g.id, g.name) for g in Grade.query.order_by(Grade.id).all()]
        self.type_of_work.choices = [(tow.id, tow.name) for tow in TypeOfWork.query.order_by(TypeOfWork.id).all()]
        self.subject.choices = [(s.id, s.name) for s in current_user.subjects]


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Электронная почта', validators=[DataRequired(), Email()])
    submit = SubmitField('Запросить сброс пароля')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Пароль', validators=[DataRequired()])
    password2 = PasswordField(
        'Повтор пароля', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Запросить сброс пароля')

class EmptyForm(FlaskForm):
    submit = SubmitField('Отправить')


class SearchForm(FlaskForm):
    search = StringField('Поиск')
    grades = SelectMultipleField('Класс/курс', choices=[])
    types_of_work = SelectMultipleField('Тип работы', choices=[])
    subjects = SelectMultipleField('Предмет', choices=[])
    submit = SubmitField('Поиск')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.grades.choices = [(g.id, g.name) for g in Grade.query.order_by(Grade.id).all()]
        self.types_of_work.choices = [(tow.id, tow.name) for tow in TypeOfWork.query.order_by(TypeOfWork.id).all()]
        self.subjects.choices = [(s.id, s.name) for s in Subject.query.order_by(Subject.id).all()]
