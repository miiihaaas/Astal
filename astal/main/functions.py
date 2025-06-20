
import calendar
from datetime import datetime, timedelta
import re, os
from time import sleep

from flask import flash, redirect, render_template, url_for
from flask_mail import Message
from astal.admin.functions import define_working_hours
from astal.models import Reservation, Settings, User, Calendar
from astal import db, mail, celery, app


def define_min_and_max_dates():
    """
    Returns a tuple containing the minimum and maximum dates available for
    reservations.

    The minimum date is tomorrow's date, and the maximum date is the last day of
    two months from today's date.
    """
    min_date = datetime.today().date() + timedelta(days=1)
    # Dva meseca unapred
    two_months_later = min_date.replace(day=1) + timedelta(days=62)
    # Poslednji dan u mesecu dva meseca unapred
    last_day_of_two_months_later = calendar.monthrange(two_months_later.year, two_months_later.month)[1]
    max_date = two_months_later.replace(day=last_day_of_two_months_later)
    return min_date, max_date


def calculate_required_tables(number_of_people):
    """
    Svaka vrednost u rečniku table_options je lista tuplova gde prvi element predstavlja broj stolova sa dva mesta, 
    a drugi element predstavlja broj stolova sa četiri mesta.
    
    funkcija vraća listu opcija (u formatu touple)
    """

    table_options = {
        1: [(1, 0), (0, 1)],                    #! 1:  ["2", "4"],
        2: [(1, 0), (0, 1)],                    #! 2:  ["2", "4"],
        3: [(0, 1), (2, 0)],                    #! 3:  ["4", "2+2"],
        4: [(0, 1), (2, 0)],                    #! 4:  ["4", "2+2"],
        5: [(0, 1), (2, 0)],                    #! 5:  ["4", "2+2"],
        6: [(1, 1), (3, 0)],                    #! 6:  ["4+2", "2+2+2"],
        7: [(1, 1), (3, 0), (0, 2)],            #! 7:  ["4+2", "2+2+2", "4+4"],
        8: [(0, 2), (2, 1), (4, 0)],            #! 8:  ["4+4", "4+(2+2)", "(2+2)+(2+2)"],
        9: [(0, 2), (2, 1), (4, 0)],            #! 9:  ["4+4", "4+(2+2)", "(2+2)+(2+2)"],
        10: [(1, 2), (3, 1), (5, 0)],           #! 10: ["4+4+2", "4+(2+2)+2", "(2+2)+(2+2)+2"],
        11: [(1, 2), (0, 3), (3, 1), (5, 0)],   #! 11: ["4+4+2", "4+4+4", "4+(2+2)+2", "(2+2)+(2+2)+2"],
        12: [(0, 3), (2, 2), (4, 1), (6, 0)]    #! 12: ["4+4+4", "4+4+(2+2)", "4+(2+2)+(2+2)", "(2+2)+(2+2)+(2+2)"]
    }
    
    return table_options.get(number_of_people, [])

def check_availability(start_time, intervals, table_options, num_intervals):
    for table_option in table_options:
        # print(f'* {table_option=}')
        start_time_found = False
        available_intervals = 0
        required_tables_2, required_tables_4 = table_option[0], table_option[1]

        for interval, details in intervals.items():
            if interval == start_time:
                start_time_found = True
            if start_time_found:
                # print(f'{num_intervals=}; {available_intervals=}')
                if details["free_tables_2"] >= required_tables_2 and details["free_tables_4"] >= required_tables_4:
                    available_intervals += 1
                    if available_intervals == num_intervals:
                        # print(f'** {interval=}')
                        # print(f'dostupno {required_tables_2=} i {required_tables_4=} za 3h - iza ovog ne bi trebalo da ima print statmenta')
                        return (True, available_intervals)
                else:
                    # print(f'*** nije dostupno {required_tables_2=} i {required_tables_4=}')
                    break  # Prekinuti unutrašnju petlju i proveriti sledeću opciju

    return (False, available_intervals)


# def get_interval_options(intervals, min_date, reservation_date, table_options, check_availability):
#     # print('* get_interval_options()')
#     time_now_obj = datetime.now()
#     interval_options = []
    
#     for interval_kay, details in intervals.items():
#         interval_kay_obj = datetime.combine(min_date, datetime.strptime(interval_kay, "%H:%M").time())
#         # print(f"{time_now_obj=}, {interval_kay_obj=}")
        
#         if reservation_date == min_date:
#             # print(f'{reservation_date=}, {min_date=}')
#             if time_now_obj < interval_kay_obj:
#                 available, available_intervals = check_availability(interval_kay, intervals, table_options, 12)
#                 if available_intervals == 12:
#                     interval_options.append([interval_kay, f''])
#                 elif available_intervals > 8:
#                     interval_options.append([interval_kay, f' - dostupno {available_intervals * 15} minuta'])
#         else:
#             available, available_intervals = check_availability(interval_kay, intervals, table_options, 12)
#             if available_intervals == 12:
#                 interval_options.append([interval_kay, f''])
#             elif available_intervals > 8:
#                 interval_options.append([interval_kay, f' - dostupno {available_intervals * 15} minuta'])
    
#     return interval_options


def get_interval_options(intervals, min_date, reservation_date, table_options, check_availability, language):
    time_now_obj = datetime.now()
    interval_options = []
    
    for interval_kay, details in intervals.items():
        interval_kay_time = datetime.strptime(interval_kay, "%H:%M").time()
        interval_kay_obj = datetime.combine(reservation_date, interval_kay_time)
        
        if reservation_date > min_date or (reservation_date == min_date and time_now_obj < interval_kay_obj):
            available, available_intervals = check_availability(interval_kay, intervals, table_options, 12)
            if available_intervals == 12:
                interval_options.append([interval_kay, interval_kay])
            elif available_intervals > 8:
                if language == 'en':
                    interval_options.append([interval_kay, f'{interval_kay} - available {available_intervals * 15} minutes'])
                else:
                    interval_options.append([interval_kay, f'{interval_kay} - dostupno {available_intervals * 15} minuta'])
    print(f'main/forms.py debug: {interval_options=}')
    return interval_options




def is_valid_user_input(form):
    user_email = form.user_email.data
    user_name = form.user_name.data
    user_surname = form.user_surname.data
    user_phone = form.user_phone.data
    user_inputs = [user_email, user_name, user_surname, user_phone]
    valid_input = True
    if not user_inputs[0]:
        # flash('Unesite email', 'danger')
        valid_input = False
    if not re.match(r"^[a-zA-Z0-9._%+-]{2,}@[a-zA-Z0-9.-]{2,}\.[a-zA-Z]{2,}$", user_inputs[0]):
        # flash('Email nije validan', 'danger')
        valid_input = False
    
    if not user_inputs[1]:
        # flash('Unesite svoje Ime', 'danger')
        valid_input = False
    if len(user_inputs[1]) < 2:
        # flash('Ime mora imati najmanje 2 slova', 'danger')
        valid_input = False

    if not user_inputs[2]:
        # flash('Unesite svoje Prezime', 'danger')
        valid_input = False
    if len(user_inputs[2]) < 3:
        # flash('Prezime mora imati najmanje 3 slova', 'danger')
        valid_input = False

    if not user_inputs[3]:
        # flash('Unesite broj telefona', 'danger')
        valid_input = False
    if user_inputs[3] and not user_inputs[3].isdigit():
        # flash('Broj telefona treba da se sastoji samo od cifara', 'danger')
        valid_input = False
    if len(user_inputs[3]) < 9 or len(user_inputs[3]) > 13:
        # flash('Broj telefona mora imati izmedju 9 i 13 cifara', 'danger')
        valid_input = False
    return valid_input

def add_user_to_db(form):
    valid_inputs = is_valid_user_input(form)
    user_email = form.user_email.data
    user_name = form.user_name.data
    user_surname = form.user_surname.data
    user_phone = form.user_phone.data
    user_inputs = [user_email, user_name, user_surname, user_phone]
    if valid_inputs:
        user = User.query.filter_by(email=user_inputs[0]).first()
        if user:
            # flash('Korisnik sa tim email adresom vec postoji', 'danger')
            user.name = user_inputs[1].title()
            user.surname = user_inputs[2].title()
            user.phone = user_inputs[3]
            db.session.commit()
            return user
        else:
            new_user = User(email=user_inputs[0], name=user_inputs[1].title(), surname=user_inputs[2].title(), phone=user_inputs[3])
            db.session.add(new_user)
            db.session.commit()
            return new_user
    else:
        return False

def create_reservation(form, user):
    settings = Settings.query.first()
    reservation_date = form.reservation_date.data
    min_date = datetime.now().date() + timedelta(days=1)
    if reservation_date < min_date:
        app.logger.warning(f"Pokušaj kreiranja rezervacije za datum u prošlosti: {reservation_date}")
        return 'invalid_date'
    number_of_people = form.number_of_people.data
    note = form.user_note.data
    # Pretpostavljamo da dobijate reservation_time iz request.form
    reservation_time = form.reservation_time.data
    app.logger.info(f' *** {reservation_date=}')
    app.logger.info(f' *** {reservation_time=}')

    # Pretvaramo reservation_time string u datetime objekat
    reservation_time_obj = datetime.strptime(reservation_time, "%H:%M")

    # Dodajemo 3 sata na reservation_time
    reservation_end_time_obj = reservation_time_obj + timedelta(hours=3)

    # Pretvaramo reservation_end_time_obj nazad u string
    reservation_end_time = reservation_end_time_obj.strftime("%H:%M")
    reservations = Reservation.query.filter_by(reservation_date=reservation_date).all()
    reservation_number = f'{reservation_date}-{(len(reservations)+1):03d}'
    new_reservation = Reservation(reservation_number=reservation_number,
                                    reservation_date=reservation_date, 
                                    number_of_people=number_of_people, 
                                    amount=int(number_of_people) * settings.reservation_coast_per_person, 
                                    start_time=reservation_time, 
                                    end_time=reservation_end_time,
                                    note=note,
                                    user_id=user.id)
    if new_reservation.user_id in [reservation.user_id for reservation in reservations if reservation.status != 'unpaid']:
        return 'duplikat'
    db.session.add(new_reservation)
    db.session.commit()
    return new_reservation


def get_or_create_reservations(form):
    reservations = Calendar.query.filter_by(date=form.reservation_date.data).first()
    if not reservations:
        new_reservations = define_working_hours(form.reservation_date.data.strftime('%Y-%m-%d'))
        db.session.add(new_reservations)
        db.session.commit()
        reservations = Calendar.query.filter_by(date=form.reservation_date.data).first()
    return reservations


def get_or_create_reservations_(new_reservation):
    reservations = Calendar.query.filter_by(date=new_reservation.reservation_date).first()
    if not reservations:
        new_reservations = define_working_hours(new_reservation.reservation_date.strftime('%Y-%m-%d'))
        db.session.add(new_reservations)
        db.session.commit()
        reservations = Calendar.query.filter_by(date=new_reservation.reservation_date).first()
    return reservations



def book_tables(start_time, intervals, reservation_id, user_id, table_options, num_intervals):
    for table_option in table_options:
        required_tables_2, required_tables_4 = table_option[0], table_option[1]
        print(f'{required_tables_2=} i {required_tables_4=}')
        start_time_found = False
        intervals_booked = 0
        can_book = True

        # Provera da li je moguće rezervisati traženi broj uzastopnih intervala
        for interval, details in intervals.items():
            if interval == start_time:
                start_time_found = True
            
            if start_time_found:
                if details["free_tables_2"] < required_tables_2 or details["free_tables_4"] < required_tables_4:
                    can_book = False
                    break

                intervals_booked += 1
                if intervals_booked == num_intervals:
                    break

        if start_time_found and can_book:
            intervals_booked = 0
            start_time_found = False  # Resetovanje za rezervaciju
            break_outer_loop = False  # Promenljiva za prekid spoljašnjeg loopa

            for interval, details in intervals.items():
                if interval == start_time:
                    start_time_found = True

                if start_time_found and intervals_booked < num_intervals:
                    details["reservations"].append({
                        "reservation_id": reservation_id,
                        "user_id": user_id,
                        "reserved_tables_2": required_tables_2, 
                        "reserved_tables_4": required_tables_4
                    })
                    details["booked_tables_2"] += required_tables_2
                    details["booked_tables_4"] += required_tables_4
                    details["free_tables_2"] -= required_tables_2
                    details["free_tables_4"] -= required_tables_4
                    intervals_booked += 1
                    print(f'rezervisan je interval {interval}')

                if intervals_booked == num_intervals:
                    print('rezervisano je maksimalan broj intervala')
                    break_outer_loop = True
                    break

            if break_outer_loop:
                break

    return intervals

#! nastavi sa istražvanjem na GPT 
#! https://chatgpt.com/g/g-cKXjWStaE-python/c/f80b28cc-e589-4fe4-9f95-f0f0cb60d85f

def send_email(user, new_reservation, language):
    settings = Settings.query.first()
    sender = settings.email_noreply
    recipients = [user.email]
    bcc = [settings.email_cc] #! staviti mejl administratora
    if language == 'mn':
        subject = f'Potvrda rezervacije ({new_reservation.reservation_number}) u restoranu {settings.restaurant_name}'
    elif language == 'en':
        subject = f'Reservation confirmation ({new_reservation.reservation_number}) at {settings.restaurant_name}'
    message = Message(subject, sender=sender, recipients=recipients, bcc=bcc)
    message.html = render_template('message_html_conformation_mail.html', 
                                    current_year=datetime.now().year,
                                    reservation=new_reservation, 
                                    settings=settings, 
                                    language=language)
    
    try:
        mail.send(message)
        # flash('Mejl je uspesno poslat', 'success')
        log_reservation_message(new_reservation)
        print('mejl je uspešno poslat')
    except Exception as e:
        flash('Greska prilikom slanja mejla: ' + str(e), 'danger')

@celery.task
def schedule_emal(reservation_id):
    print(f'* pokrenut je Celery: {reservation_id=}')
    with app.app_context():
        reservation = Reservation.query.get(reservation_id)
        if reservation:
            subject = f'Podsetnik rezervacije - {reservation.reservation_number}'
            recipients = [reservation.user.email]
            cc = [] #! staviti mejl administratora
            body = f'Rezervacija {reservation.reservation_number} počinje uskoro. Podsećamo vas da će rezervacija početi u {reservation.start_time} na datum {reservation.reservation_date}.'
            message = Message(subject, recipients=recipients, cc=cc)
            message.html = body
    
        try:
            mail.send(message)
        except Exception as e:
            print('Greska prilikom slanja mejla: ' + str(e), 'danger')


@celery.task
def test():
    print('** Test celery task **')
    sleep(10)
    print('posle 10 sekundi')
    return('Test je uspešno izvršen')


def log_reservation_message(new_reservation):
    '''
    Kreira novi log fajl u folderu app_logs/reservations_data u kome skladišti neophodne informacije o rezervaciji
    i proverava validnost datuma rezervacije
    '''

    # Kreiranje direktorijuma za pojedinačne logove rezervacija
    base_dir = os.path.join(os.getcwd(), 'app_logs', 'reservations_data')
    os.makedirs(base_dir, exist_ok=True)
    
    # Kreiranje log fajla za konkretnu rezervaciju
    log_file = os.path.join(base_dir, f'{new_reservation.reservation_number}.log')
    now = datetime.now()
    now_str = now.strftime('%Y-%m-%d %H:%M:%S')
    
    # Provera validnosti datuma rezervacije
    min_date = datetime.today().date() + timedelta(days=1)
    reservation_date = new_reservation.reservation_date
    reservation_date_str = reservation_date.strftime('%Y-%m-%d')
    
    # Logovanje informacija o rezervaciji
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write("\n==============================\n")
        f.write(f'{now_str} - Rezervacija {new_reservation.reservation_number} je kreirana\n')
        f.write(f'Broj osoba: {new_reservation.number_of_people}\n')
        f.write(f'Datum rezervacije: {reservation_date_str}\n')
        f.write(f'Minimalni datum za rezervaciju: {min_date}\n')
        
        # Provera da li je datum rezervacije u prošlosti
        if reservation_date < min_date:
            warning_msg = f'UPOZORENJE: Datum rezervacije ({reservation_date_str}) je u prošlosti u odnosu na minimalni datum za rezervaciju ({min_date})!\n'
            f.write(warning_msg)
            app.logger.warning(f'Kreirana je rezervacija za datum u prošlosti! Broj rezervacije: {new_reservation.reservation_number}, Datum rez: {reservation_date_str}, Minimalni datum rezervacije: {min_date}')
        
        f.write(f'Vreme početka: {new_reservation.start_time}\n')
        f.write(f'Vreme kraja: {new_reservation.end_time}\n')
        f.write(f'Napomena: {new_reservation.note}\n')
        f.write(f'Vreme kreiranja: {new_reservation.timestamp}\n')
        f.write("\n==============================\n")
    
