import re
from flask_wtf import FlaskForm
from wtforms import DateField, IntegerField, SelectField, StringField, TextAreaField, SubmitField, EmailField
from wtforms.validators import ValidationError, DataRequired, NumberRange


PHONE_MIN_DIGITS = 8
PHONE_MAX_DIGITS = 15 #! E.164 maksimum
PHONE_EXAMPLE = '+382 68 123 456'


def normalize_phone(raw):
    """
    Ciscenje broja telefona u jedinstven format: '+' + cifre.
    '+382 68 123-456' i '0038268123456' oba daju '+38268123456'.
    """
    if not raw:
        return ''
    cleaned = re.sub(r'[\s\-\(\)\./]', '', raw.strip())
    if cleaned.startswith('00'):
        cleaned = '+' + cleaned[2:]
    return cleaned


def is_valid_phone(raw):
    """Broj je validan samo ako sadrzi pozivni broj zemlje."""
    phone = normalize_phone(raw)
    if not phone.startswith('+'):
        return False
    digits = phone[1:]
    if not digits.isdigit():
        return False
    return PHONE_MIN_DIGITS <= len(digits) <= PHONE_MAX_DIGITS


class ReservationFormEnglish(FlaskForm):
    reservation_date = DateField('Select Date', validators=[])
    number_of_people = IntegerField('Number of People', validators=[DataRequired(), NumberRange(min=1, max=12)])
    reservation_time = SelectField('Select Reservation Time', validators=[], choices=[])
    user_email = EmailField('Email', validators=[])
    user_name = StringField('First Name', validators=[])
    user_surname = StringField('Last Name', validators=[])
    user_phone = StringField('Phone number (including the country prefix)', validators=[])
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
        phone = normalize_phone(field.data)
        if not phone.startswith('+') or not phone[1:].isdigit():
            raise ValidationError(f'Please enter the number including the country prefix, for example {PHONE_EXAMPLE}.')
        if not PHONE_MIN_DIGITS <= len(phone[1:]) <= PHONE_MAX_DIGITS:
            raise ValidationError(f'The phone number must contain between {PHONE_MIN_DIGITS} and {PHONE_MAX_DIGITS} digits.')
        field.data = phone

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
    user_phone = StringField('Broj telefona (sa pozivnim brojem zemlje)', validators=[])
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
        phone = normalize_phone(field.data)
        if not phone.startswith('+') or not phone[1:].isdigit():
            raise ValidationError(f'Unesite broj sa pozivnim brojem zemlje, na primjer {PHONE_EXAMPLE}.')
        if not PHONE_MIN_DIGITS <= len(phone[1:]) <= PHONE_MAX_DIGITS:
            raise ValidationError(f'Broj telefona mora imati između {PHONE_MIN_DIGITS} i {PHONE_MAX_DIGITS} cifara.')
        field.data = phone
    
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
    user_phone = StringField('Broj telefona (sa pozivnim brojem zemlje)', validators=[])
    user_note = TextAreaField('Napomena')


class PaymentFormEnglish(FlaskForm):
    reservation_date = DateField('Reservation date', validators=[])
    number_of_people = IntegerField('Number of people', validators=[DataRequired(), NumberRange(min=1, max=12)])
    amount = StringField('Reservation cost', validators=[])
    reservation_time = StringField('Reservation time', validators=[])
    user_email = EmailField('Email', validators=[])
    user_name = StringField('Name', validators=[])
    user_surname = StringField('Surname', validators=[])
    user_phone = StringField('Phone number (including the country prefix)', validators=[])
    user_note = TextAreaField('Note')
