
from datetime import datetime
from flask import Blueprint, redirect, render_template, flash, request, url_for
from astal import db
from astal.models import User, Reservation, Calendar
from astal.main.functions import check_availability, calculate_required_tables, is_valid_user_input, add_user_to_db, define_min_and_max_dates


main = Blueprint('main', __name__)


@main.route('/', methods=['GET', 'POST'])
def home():
    min_date, max_date = define_min_and_max_dates()
    print(f'{min_date=}')
    if request.method == 'POST':
        submit_type = request.form.get('submit_type')
        print(f'{submit_type=}')
        reservation_date = request.form.get('reservation_date')
        number_of_people = int(request.form.get('number_of_people'))
        print(f'{reservation_date=}')
        print(f'{number_of_people=}')
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

            user_inputs = [user_email, user_name, user_surname, user_phone]
            if is_valid_user_input(user_inputs):
                user = add_user_to_db(user_inputs)
            else:
                return redirect(url_for('main.home'))
            
            
            reservation_time = request.form.get('reservation_time')
            new_reservation = Reservation(reservation_date=datetime.strptime(reservation_date, '%Y-%m-%d').date(), 
                                            number_of_people=number_of_people, 
                                            amount=int(number_of_people)*5, 
                                            start_time=reservation_time, 
                                            end_time="13:00", #! ovo napravi dinamično
                                            user_id=user.id)
            db.session.add(new_reservation)
            db.session.commit()
            return f'pritisnuto je dugme REZERVIŠI'
        elif submit_type == 'input_change':
            reservations = Calendar.query.filter_by(date=datetime.strptime(reservation_date, '%Y-%m-%d').date()).all()
    elif request.method == 'GET':
        reservation_date = min_date
        number_of_people = 1
        reservations = Calendar.query.filter_by(date=min_date).all()
    # print(f'{reservations=}')
    required_tables = calculate_required_tables(number_of_people)
    intervals = reservations[0].intervals
    print(f'{intervals=}')
    interval_options = []
    for interval_kay, details in intervals.items():
        # print(f'* {interval_kay=}')
        aveilable, available_intervals = check_availability(interval_kay, intervals, required_tables, 4)
        if available_intervals > 2:
            print(f'{interval_kay=}. dostupno {available_intervals * 15} minuta')
            interval_options.append([interval_kay, f'dostupno {available_intervals * 15} minuta'])
        else:
            print(f'{interval_kay=}. nedostupno')
            interval_options.append([interval_kay, 'nedostupno'])
    print(f'{interval_options=}')
    
    return render_template('home.html', 
                            min_date=min_date, 
                            max_date=max_date,
                            reservation_date=reservation_date,
                            number_of_people=number_of_people,
                            interval_options=interval_options)

@main.route('/time/<data>', methods=['GET', 'POST'])
def time(data):
    print(f'{data=}')
    # interval_options = data['interval_options']
    
    return render_template('time.html')