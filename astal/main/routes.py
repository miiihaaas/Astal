
from datetime import datetime, timedelta
import hashlib
import os
from flask import Blueprint, json, jsonify, redirect, render_template, flash, request, url_for
from flask_login import current_user
from astal import db
from astal.admin.functions import create_working_intervals, define_working_hours
from astal.main.forms import PaymentFormEnglish, PaymentFormSerbian, ReservationFormEnglish, ReservationFormSerbian
from astal.models import Settings, User, Reservation, Calendar
from astal.main.functions import book_tables, check_availability, calculate_required_tables, create_reservation, get_interval_options, get_or_create_reservations, get_or_create_reservations_, is_valid_user_input, add_user_to_db, define_min_and_max_dates, schedule_emal, send_email, test


main = Blueprint('main', __name__)


@main.route('/settings', methods=['GET', 'POST'])
def settings():
    settings = Settings.query.first()
    if current_user.is_anonymous:
        flash('Nemate autorizaciju da pristupite ovoj stranici.', 'danger')
        return redirect(url_for('main.home'))
    if request.method == 'POST':
        settings.reservation_coast_per_person = float(request.form.get('reservation_coast_per_person'))
        settings.default_number_of_tables_2 = int(request.form.get('default_number_of_tables_2'))
        settings.default_number_of_tables_4 = int(request.form.get('default_number_of_tables_4'))
        db.session.commit()
        flash('Uspešno ste izmenili podešavanja.', 'success')
        return redirect(url_for('main.settings'))
    return render_template('settings.html', 
                            settings=settings, 
                            title=f'{settings.restaurant_name} - Podešavanja')


@main.route('/under_construction')
def under_construction():
    settings = Settings.query.first()
    return render_template('under_construction.html',
                            settings=settings)

@main.route('/')
def index():
    # return redirect(url_for('main.under_construction'))
    return redirect(url_for('main.home', language='mn'))

@main.route('/<string:language>', methods=['GET', 'POST'])
def home(language):
    settings = Settings.query.first()
    if language == 'mn':
        form = ReservationFormSerbian()
    elif language == 'en':
        form = ReservationFormEnglish()
    else:
        return redirect(url_for('main.home', language='mn'))
    # return redirect(url_for('main.under_construction')) #! se menja nešto na sajtu -- uncomment
    min_date, max_date = define_min_and_max_dates()
    print(f'{min_date=}')
    if not request.method == 'GET':
        number_of_people = int(request.form.get('number_of_people'))
        reservations = get_or_create_reservations(form)
        table_options = calculate_required_tables(number_of_people)
        intervals = json.loads(reservations.intervals)
        interval_options = get_interval_options(intervals, min_date, form.reservation_date.data, table_options, check_availability, language)
        form.reservation_time.choices = interval_options
    if request.method == 'POST':
    # if form.validate_on_submit():
        # print(f'forma je validna')
        submit_type = request.form.get('submit_type')
        reservation_date = form.reservation_date.data
        number_of_people = int(form.number_of_people.data)
        # number_of_people = int(request.form.get('number_of_people'))
        if not reservation_date:
            flash('Unesite datum rezervacije', 'danger')
            return redirect(url_for('main.home'))
        if not number_of_people:
            flash('Unesite broj osoba', 'danger')
            return redirect(url_for('main.home'))
        if submit_type == 'button':
            '''
            pritisnuto je dugme rezerviši:
            1. proveri ima li mejl korisnika u db
            2. ako nema mejl u db, dodaj korisnika u db
            3. sačuvaj rezervaciju (urađeno)
            4. ažuriraj kalendar na dati datum
            '''
            if not form.validate():
                # for field, errors in form.errors.items():
                #     for error in errors:
                #         flash(f'**** {error}', 'danger')
                print(f' **** forma Nije validna')
                reservations = get_or_create_reservations(form)
                table_options = calculate_required_tables(number_of_people)
                intervals = json.loads(reservations.intervals)
                interval_options = get_interval_options(intervals, min_date, form.reservation_date.data, table_options, check_availability, language)
                form.reservation_time.choices = interval_options
                # flash(f'{form.errors}', 'danger')
                return render_template('home.html', 
                                        form=form, 
                                        min_date=min_date, 
                                        max_date=max_date, 
                                        number_of_people=number_of_people, 
                                        reservation_date=reservation_date,
                                        interval_options=interval_options,
                                        title=f'{settings.restaurant_name} - Rezervacija',
                                        settings=settings,
                                        language=language)
            else:
                print(f'**** forma je validna')
                # if is_valid_user_input(form):
                #     user = add_user_to_db(form)
                # else:
                #     return redirect(url_for('main.home', language=language))
                # return "napravi funkcionalnost da se vrati na istu formu da se zadrže sva uneta polja"
                # new_reservation = create_reservation(form, user)
                # print(f'*** {new_reservation=}')
                # if new_reservation == 'duplikat':
                #     if language == 'mn':
                #         flash('Već ste rezervisali sto za ovaj dan. Ukoliko imate dodatna pitanja, molmio Vas kontaktirajte nas na +382 68 333 444.', 'info')
                #     elif language == 'en':
                #         flash('You have already reserved a table for this day. If you have additional needs, please contact us at +382 68 333 444.', 'info')
                #     return redirect(url_for('main.home', language=language))
                # Redirect to payment_form route with POST request
                return redirect(url_for('main.payment_form', language=language), code=307)

        elif submit_type == 'input_change':
            print('izmena datuma ili broja osoba')
            # reservation_date=datetime.strptime(reservation_date, '%Y-%m-%d').date()
            print(f'{reservation_date=}')
            reservations = get_or_create_reservations(form)
            table_options = calculate_required_tables(number_of_people)
            intervals = json.loads(reservations.intervals)
            interval_options = get_interval_options(intervals, min_date, reservation_date, table_options, check_availability, language)
            form.reservation_time.choices = interval_options
        return render_template('home.html', 
                                form=form,
                                min_date=min_date, 
                                max_date=max_date,
                                reservation_date=reservation_date,
                                number_of_people=number_of_people,
                                interval_options=interval_options,
                                title=f'{settings.restaurant_name} - Rezervacije',
                                settings=settings,
                                language=language)

    elif request.method == 'GET':
        form.reservation_date.data = min_date
        form.number_of_people.data = 1
        number_of_people = 1
        reservations = get_or_create_reservations(form)
    table_options = calculate_required_tables(number_of_people)
    intervals = json.loads(reservations.intervals)
    interval_options = get_interval_options(intervals, min_date, form.reservation_date.data, table_options, check_availability, language)
    form.reservation_time.choices = interval_options
    return render_template('home.html',
                            form=form, 
                            min_date=min_date, 
                            max_date=max_date,
                            # reservation_date=form.reservation_date.data,
                            number_of_people=number_of_people,
                            interval_options=interval_options,
                            title=f'{settings.restaurant_name} - Rezervacije',
                            settings=settings,
                            language=language)


@main.route('/payment_form/<string:language>', methods=['GET', 'POST'])
def payment_form(language):
    settings = Settings.query.first()
    if language == 'mn':
        form = PaymentFormSerbian()
    elif language == 'en':
        form = PaymentFormEnglish()

    if is_valid_user_input(form):
        user = add_user_to_db(form)
    else:
        return redirect(url_for('main.home', language=language))
    new_reservation = create_reservation(form, user)
    print(f'*** {new_reservation=}')
    if new_reservation == 'duplikat':
        if language == 'mn':
            flash('Već ste rezervisali sto za ovaj dan. Ukoliko imate dodatna pitanja, molmio Vas kontaktirajte nas na +382 68 333 444.', 'info')
        elif language == 'en':
            flash('You have already reserved a table for this day. If you have additional needs, please contact us at +382 68 333 444.', 'info')
        return redirect(url_for('main.home', language=language))
    elif new_reservation == 'invalid_date':
        if language == 'mn':
            flash('Nije moguće rezervisati sto za dan pre danasnjeg. Ukoliko imate dodatna pitanja, molmio Vas kontaktirajte nas na +382 68 333 444.', 'info')
        elif language == 'en':
            flash('You cannot reserve a table for a day before today. If you have additional needs, please contact us at +382 68 333 444.', 'info')
        return redirect(url_for('main.home', language=language))
    
    print(f'{request.form=}')
    form.reservation_date.data = request.form.get('reservation_date')
    form.number_of_people.data = request.form.get('number_of_people')
    form.amount.data = int(request.form.get('number_of_people')) * settings.reservation_coast_per_person
    form.reservation_time.data = request.form.get('reservation_time')
    form.user_email.data = request.form.get('user_email')
    form.user_name.data = request.form.get('user_name')
    form.user_surname.data = request.form.get('user_surname')
    form.user_phone.data = request.form.get('user_phone')
    form.user_note.data = request.form.get('user_note')
    
    #! WSPAY data
    wspay_shop_id = os.getenv('WSPAY_SHOPID')
    wspay_sekret_key = os.getenv('WSPAY_SEKRET_KEY')
    total_amoount = f'{form.amount.data:.2f}'.replace('.', '').replace(',', '') #! primer 17,35 je 1735
    print(f'{total_amoount=}')
    print(f'{new_reservation.id=}')
    
    string_to_hash = f'{wspay_shop_id}{wspay_sekret_key}{str(new_reservation.id)}{wspay_sekret_key}{total_amoount}{wspay_sekret_key}'
    # Generiranje SHA-512 hasha
    signature = hashlib.sha512(string_to_hash.encode('utf-8')).hexdigest()
    print(f'{string_to_hash=}')
    print(f'{signature=}')
    
    wspay_data = {
        'ShopID': os.getenv('WSPAY_SHOPID'),
        'ShoppingCartID': str(new_reservation.id),
        'TotalAmount': f'{form.amount.data:.2f}'.replace('.', ','),
        'Signature': signature
    }
    
    return render_template('payment_form.html',
                            settings=settings,
                            form=form,
                            language=language,
                            wspay_data=wspay_data)
                
@main.route('/conformation/<string:language>', methods=['GET', 'POST'])
def conformation(language):
    settings = Settings.query.first()
    reservation_id = request.args.get('ShoppingCartID')
    approval_code = request.args.get('ApprovalCode')
    recived_signature = request.args.get('Signature')
    
    new_reservation = Reservation.query.get_or_404(reservation_id)
    user = User.query.get_or_404(new_reservation.user_id)
    
    number_of_people = int(new_reservation.number_of_people)
    reservation_date = new_reservation.reservation_date
    
    #! WSPAY data
    wspay_shop_id = os.getenv('WSPAY_SHOPID')
    wspay_sekret_key = os.getenv('WSPAY_SEKRET_KEY')
    success = 1
    
    string_to_hash = f'{wspay_shop_id}{wspay_sekret_key}{str(new_reservation.id)}{wspay_sekret_key}{success}{wspay_sekret_key}{approval_code}{wspay_sekret_key}'
    # Generiranje SHA-512 hasha
    signature = hashlib.sha512(string_to_hash.encode('utf-8')).hexdigest()
    app.logger.info(f'{string_to_hash=}')
    app.logger.info(f'{signature=}')
    
    if recived_signature != signature:
        if language == 'mn':
            flash('Nije validno', 'danger')
        elif language == 'en':
            flash('Signature is not valid', 'danger')
        return redirect(url_for('main.home', language=language))
    
    
    send_email(user, new_reservation, language)
    app.logger.info(f'prvi mejl bi trebalo da stigne oko {datetime.now()=}')
    #!
    # reservation_datetime = datetime.combine(
    #     new_reservation.reservation_date,
    #     datetime.strptime(new_reservation.start_time, "%H:%M").time()
    # )
    # email_time = reservation_datetime - timedelta(hours=3)
    # print(f'drugi mejl bi trebalo da stigne u {email_time=}')
    # schedule_emal.apply_async(args=[new_reservation.id], eta=email_time)
    # print(f'ovo je info iza funkcije shedule_mail: args={new_reservation.id=}, eta={email_time=}')
    # # test.delay()
    #!
    
    new_reservation.status = 'pending'
    
    # reservations = get_or_create_reservations(form)
    reservations = get_or_create_reservations_(new_reservation)
    table_options = calculate_required_tables(number_of_people)
    
    updated_intervals = book_tables(new_reservation.start_time, json.loads(reservations.intervals), new_reservation.id, user.id, table_options, 12)
    reservations.intervals = json.dumps(updated_intervals)
    try:
        db.session.commit()
        print('Data successfully updated in the database.')
    except Exception as e:
        db.session.rollback()
        print(f'Error during commit: {e}')
    if language == 'mn':
        flash(f'Uspešno ste napravili rezervaciju. Informacije o rezervaciji će stići na Vašu email adresu.', 'success')
    else:
        flash(f'You have successfully made a reservation. The reservation information will be sent to your email address.', 'success')
    return render_template('conformation_page.html', 
                            reservation_number=new_reservation.reservation_number,
                            reservation_date=reservation_date, #!
                            reservation_time=new_reservation.start_time,
                            number_of_people=number_of_people,
                            note=new_reservation.note,
                            title=f'{settings.restaurant_name} - Rezervacije',
                            settings=settings,
                            language=language)


@main.route('/conformation_local/<string:language>/<int:reservation_id>', methods=['GET', 'POST'])
def conformation_local(language, reservation_id):
    settings = Settings.query.first()
    
    new_reservation = Reservation.query.get_or_404(reservation_id)
    user = User.query.get_or_404(new_reservation.user_id)
    
    number_of_people = int(new_reservation.number_of_people)
    reservation_date = new_reservation.reservation_date

    
    
    send_email(user, new_reservation, language)
    app.logger.info(f'prvi mejl bi trebalo da stigne oko {datetime.now()=}')
    
    new_reservation.status = 'pending'
    
    # reservations = get_or_create_reservations(form)
    reservations = get_or_create_reservations_(new_reservation)
    table_options = calculate_required_tables(number_of_people)
    
    updated_intervals = book_tables(new_reservation.start_time, json.loads(reservations.intervals), new_reservation.id, user.id, table_options, 12)
    reservations.intervals = json.dumps(updated_intervals)
    try:
        db.session.commit()
        print('Data successfully updated in the database.')
    except Exception as e:
        db.session.rollback()
        print(f'Error during commit: {e}')
    if language == 'mn':
        flash(f'Uspešno ste napravili rezervaciju. Informacije o rezervaciji će stići na Vašu email adresu.', 'success')
    else:
        flash(f'You have successfully made a reservation. The reservation information will be sent to your email address.', 'success')
    return render_template('conformation_page.html', 
                            reservation_number=new_reservation.reservation_number,
                            reservation_date=reservation_date, #!
                            reservation_time=new_reservation.start_time,
                            number_of_people=number_of_people,
                            note=new_reservation.note,
                            title=f'{settings.restaurant_name} - Rezervacije',
                            settings=settings,
                            language=language)


@main.route('/cancel_url/<string:language>', methods=['GET'])
def cancel_url(language):
    if language == 'mn':
        flash('Rezervacijata je prekinuta.', 'danger')
    elif language == 'en':
        flash('The reservation has been canceled.', 'danger')
    return redirect(url_for('main.home', language=language))


@main.route('/return_error_url/<string:language>', methods=['GET'])
def return_error_url(language):
    if language == 'mn':
        flash('Nastala je greška prilikom kreiranja rezervacije.', 'danger')
    elif language == 'en':
        flash('An error occurred while creating the reservation.', 'danger')
    return redirect(url_for('main.home', language=language))