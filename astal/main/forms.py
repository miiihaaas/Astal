import re
from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField, StringField, TextAreaField, SubmitField, EmailField
from wtforms.validators import ValidationError, DataRequired, NumberRange


class ReservationFormEnglish(FlaskForm):
    reservation_date = DateField('Select Date', validators=[])
    number_of_people = IntegerField('Number of People', validators=[DataRequired(), NumberRange(min=1, max=12)])
    reservation_time = SelectField('Select Reservation Time', validators=[], choices=[])
    user_email = EmailField('Email', validators=[])
    user_name = StringField('First Name', validators=[])
    user_surname = StringField('Last Name', validators=[])
    user_phone = StringField('Phone Number', validators=[])
    user_note = TextAreaField('Note')
    submit = SubmitField('Reserve')

    def validate_number_of_people(form, field):
        if field.data < 1 or field.data > 12:
            raise ValidationError('The number of people must be between 1 and 12.')

    def validate_user_email(form, field):
        if not field.data:
            raise ValidationError('Please enter your email address.')
        if not re.match(r'^[a-zA-Z0-9._%+-]{2,}@[a-zA-Z0-9.-]{2,}\.[a-zA-Z]{2,}$', field.data):
            raise ValidationError('Please enter a valid email address.') 

    def validate_user_phone(form, field):
        if not field.data:
            raise ValidationError('Please enter your phone number.')
        if not field.data.isdigit():
            raise ValidationError('The phone number must contain only digits.')
        if len(field.data) < 9 or len(field.data) > 13:
            raise ValidationError('The phone number must be between 9 and 13 digits.')

    def validate_user_name(form, field):
        if not field.data:
            raise ValidationError('Please enter your first name.')
        if len(field.data) < 2:
            raise ValidationError('The first name must be at least 2 characters long.')

    def validate_user_surname(form, field):
        if not field.data:
            raise ValidationError('Please enter your last name.')
        if len(field.data) < 2:
            raise ValidationError('The last name must be at least 2 characters long.')



class ReservationFormSerbian(FlaskForm):
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


class PaymentFormSerbian(FlaskForm):
    reservation_date = DateField('Datum rezervacije', validators=[])
    number_of_people = IntegerField('Broj osoba', validators=[DataRequired(), NumberRange(min=1, max=12)])
    amount = StringField('Cena rezervacije', validators=[])
    reservation_time = StringField('Vreme rezervacije', validators=[])
    user_email = EmailField('Mejl', validators=[])
    user_name = StringField('Ime', validators=[])
    user_surname = StringField('Prezime', validators=[])
    user_phone = StringField('Broj telefona', validators=[])
    user_note = TextAreaField('Napomena')


class PaymentFormEnglish(FlaskForm):
    reservation_date = DateField('Reservation date', validators=[])
    number_of_people = IntegerField('Number of people', validators=[DataRequired(), NumberRange(min=1, max=12)])
    amount = StringField('Reservation cost', validators=[])
    reservation_time = StringField('Reservation time', validators=[])
    user_email = EmailField('Email', validators=[])
    user_name = StringField('Name', validators=[])
    user_surname = StringField('Surname', validators=[])
    user_phone = StringField('Phone number', validators=[])
    user_note = TextAreaField('Note')
