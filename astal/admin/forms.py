from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError


class LoginForm(FlaskForm):
    email = StringField('Mejl', validators=[DataRequired(), Email()])
    password = PasswordField('Lozinka', validators=[DataRequired()])
    remember = BooleanField('Zapamti me')
    submit = SubmitField('Prijavite se')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Mejl', validators=[DataRequired(), Email()])
    submit = SubmitField('Pošalji instrukcije')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nova lozinka', validators=[DataRequired()])
    confirm_password = PasswordField('Ponovite lozinku', validators=[DataRequired(), EqualTo('password', message='Lozinke se moraju poklapati.')])
    submit = SubmitField('Promeni lozinku')