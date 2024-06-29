
from datetime import datetime, timedelta
from flask import Blueprint, json, jsonify, redirect, render_template, flash, request, url_for
from flask_login import current_user
from astal import db
from astal.admin.functions import create_working_intervals, define_working_hours
from astal.models import Settings, User, Reservation, Calendar
from astal.main.functions import book_tables, check_availability, calculate_required_tables, get_interval_options, is_valid_user_input, add_user_to_db, define_min_and_max_dates, schedule_emal, send_email, test


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
        flash('Uspesno ste izmenili postavke', 'success')
        return redirect(url_for('main.settings'))
    return render_template('settings.html', settings=settings)


@main.route('/', methods=['GET', 'POST'])
def home():
    settings = Settings.query.first()
    min_date, max_date = define_min_and_max_dates()
    print(f'{min_date=}')
    if request.method == 'POST':
        submit_type = request.form.get('submit_type')
        reservation_date = request.form.get('reservation_date')
        number_of_people = int(request.form.get('number_of_people'))
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
            user_email = request.form.get('user_email')
            user_name = request.form.get('user_name')
            user_surname = request.form.get('user_surname')
            user_phone = request.form.get('user_phone')
            note = request.form.get('user_note')

            user_inputs = [user_email, user_name, user_surname, user_phone]
            if is_valid_user_input(user_inputs):
                user = add_user_to_db(user_inputs)
            else:
                return "napravi funkcionalnost da se vrati na istu formu da se zadrže sva uneta polja"
            
            
            # Pretpostavljamo da dobijate reservation_time iz request.form
            reservation_time = request.form.get('reservation_time')  # npr. "14:00"

            # Pretvaramo reservation_time string u datetime objekat
            reservation_time_obj = datetime.strptime(reservation_time, "%H:%M")

            # Dodajemo 3 sata na reservation_time
            reservation_end_time_obj = reservation_time_obj + timedelta(hours=3)

            # Pretvaramo reservation_end_time_obj nazad u string
            reservation_end_time = reservation_end_time_obj.strftime("%H:%M")
            reservations = Reservation.query.filter_by(reservation_date=datetime.strptime(reservation_date, '%Y-%m-%d').date()).all()
            reservation_number = f'{reservation_date}-{(len(reservations)+1):03d}'
            new_reservation = Reservation(reservation_number=reservation_number,
                                            reservation_date=datetime.strptime(reservation_date, '%Y-%m-%d').date(), 
                                            number_of_people=number_of_people, 
                                            amount=int(number_of_people) * settings.reservation_coast_per_person, 
                                            start_time=reservation_time, 
                                            end_time=reservation_end_time,
                                            note=note,
                                            user_id=user.id)
            db.session.add(new_reservation)
            db.session.commit()
            send_email(user, new_reservation)
            print(f'prvi mejl bi trebalo da stigne oko {datetime.now()=}')
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
            
            reservations = Calendar.query.filter_by(date=datetime.strptime(reservation_date, '%Y-%m-%d').date()).first()
            if not reservations:
                new_reservations = define_working_hours(settings, reservation_date)
                db.session.add(new_reservations)
                db.session.commit()
                reservations = Calendar.query.filter_by(date=datetime.strptime(reservation_date, '%Y-%m-%d').date()).first()

            table_options = calculate_required_tables(number_of_people)
            # print(f'* pre izmene: {reservations.intervals=}')
            print(f'* pre izmene: {type(reservations.intervals)=}')
            updated_intervals = book_tables(reservation_time, json.loads(reservations.intervals), new_reservation.id, user.id, table_options, 12)
            reservations.intervals = json.dumps(updated_intervals)
            print(f'{reservations.id=}')
            # print(f'** nakon izmene: {reservations.intervals=}')
            print(f'** nakon izmene: {type(reservations.intervals)=}')
            try:
                db.session.commit()
                print('Data successfully updated in the database.')
            except Exception as e:
                db.session.rollback()
                print(f'Error during commit: {e}')
            
            # if blok za padeže u flash
            if number_of_people == 1:
                osoba = "osobu"
            elif number_of_people < 5:
                osoba = "osobe"
            else:
                osoba = "osoba"
            flash(f'Uspesno ste napravili rezervaciju za {number_of_people} {osoba}. Rezervacija se odnosi na datum {reservation_date} u {reservation_time}', 'success')
            return render_template('conformation_page.html', reservation_number=reservation_number)
        elif submit_type == 'input_change':
            print('izmena datuma ili broja osoba')
            # reservation_date=datetime.strptime(reservation_date, '%Y-%m-%d').date()
            print(f'{reservation_date=}')
            reservations = Calendar.query.filter_by(date=datetime.strptime(reservation_date, '%Y-%m-%d').date()).first()
            print(f'{reservations=}')
            if not reservations:
                new_reservations = define_working_hours(settings, reservation_date)
                db.session.add(new_reservations)
                db.session.commit()
                reservations = Calendar.query.filter_by(date=datetime.strptime(reservation_date, '%Y-%m-%d').date()).first()
            table_options = calculate_required_tables(number_of_people)
            intervals = json.loads(reservations.intervals)
            # print(f'{intervals=}'))
            interval_options = get_interval_options(intervals, min_date, datetime.strptime(reservation_date, '%Y-%m-%d').date(), table_options, check_availability)
        return render_template('home.html', 
                    min_date=min_date, 
                    max_date=max_date,
                    reservation_date=reservation_date,
                    number_of_people=number_of_people,
                    interval_options=interval_options)
    elif request.method == 'GET':
        reservation_date = min_date
        number_of_people = 1
        reservations = Calendar.query.filter_by(date=min_date).first()
        if not reservations:
            new_reservations = define_working_hours(settings, reservation_date.strftime('%Y-%m-%d'))
            db.session.add(new_reservations)
            db.session.commit()
            reservations = Calendar.query.filter_by(date=min_date).first()
    # print(f'{reservations=}')
    table_options = calculate_required_tables(number_of_people)
    intervals = json.loads(reservations.intervals)
    # print(f'{intervals=}')
    interval_options = get_interval_options(intervals, min_date, reservation_date, table_options, check_availability)
    
    return render_template('home.html', 
                            min_date=min_date, 
                            max_date=max_date,
                            reservation_date=reservation_date,
                            number_of_people=number_of_people,
                            interval_options=interval_options)
    

# @main.route('/celery_test/<int:repetitions>', methods=['GET', 'POST'])
# def celery_test(repetitions):
#     for i in range(repetitions):
#         print(f'* iteracija broj {i}')
#         test.delay()
#     return 'celery test'
