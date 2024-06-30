import re
from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField, StringField, TextAreaField, SubmitField, EmailField
from wtforms.validators import ValidationError, DataRequired, NumberRange


class ReservationForm(FlaskForm):
    reservation_date = DateField('Izaberite datum', validators=[])
    number_of_people = IntegerField('Broj osoba', validators=[DataRequired(), NumberRange(min=1, max=12)])
    reservation_time = SelectField('Izaberite vreme rezervacije', validators=[], choices=[])
    user_email = EmailField('Mejl', validators=[])
    user_name = StringField('Ime', validators=[])
    user_surname = StringField('Prezime', validators=[])
    user_phone = StringField('Broj telefona', validators=[])
    user_note = TextAreaField('Napomena')
    submit = SubmitField('Rezervišite')

    def validate_number_of_people(form, field):
        if field.data < 1 or field.data > 12:
            raise ValidationError('Broj osoba može biti između 1 i 12.')

    def validate_user_email(form, field):
        if not field.data:
            raise ValidationError('Unesite mejl adresu.')
        if not re.match(r'^[a-zA-Z0-9._%+-]{2,}@[a-zA-Z0-9.-]{2,}\.[a-zA-Z]{2,}$', field.data):
            raise ValidationError('Unesite validnu mejl adresu.') 

    def validate_user_phone(form, field):
        if not field.data:
            raise ValidationError('Unesite broj telefona.')
        if not field.data.isdigit():
            raise ValidationError('Broj telefona mora sadržati samo cifre.')
        if len(field.data) < 9 or len(field.data) > 13:
            raise ValidationError('Broj telefona mora imati između 9 i 13 cifara.')
    
    def validate_user_name(form, field):
        if not field.data:
            raise ValidationError('Unesite svoje ime.')
        if len(field.data) < 2:
            raise ValidationError('Ime mora imati najmanje 2 slova.')

    def validate_user_surname(form, field):
        if not field.data:
            raise ValidationError('Unesite svoje prezime.')
        if len(field.data) < 2:
            raise ValidationError('Prezime mora imati najmanje 2 slova.')
