from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, widgets
from wtforms.fields.choices import SelectMultipleField
from wtforms.fields.simple import TextAreaField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length
import sqlalchemy as sa
from app import db
from app.models import Teacher, Subject, EducationalInstitution


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
    educational_institution = SelectField('Учебное заведение', validators=[DataRequired()], choices=[])
    submit = SubmitField('Зарегистрироваться')

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)

        self.subjects.choices = [(sub.id, sub.name) for sub in Subject.query.all()]
        self.educational_institution.choices = [(ei.id, ei.name) for ei in EducationalInstitution.query.all()]

    def validate_username(self, username):
        user = db.session.scalar(sa.select(Teacher).where(
            Teacher.username == username.data))
        if user is not None:
            raise ValidationError('Пожалуйста, используйте другой логин')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(Teacher).where(
            Teacher.email == email.data))
        if user is not None:
            raise ValidationError('Пожалуйста, используйте другой почтовый адрес')
