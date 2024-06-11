
import calendar
from datetime import datetime, timedelta

from flask import flash, redirect, url_for
from flask_mail import Message
from astal.models import User
from astal import db, mail


def define_min_and_max_dates():
    """
    Returns a tuple containing the minimum and maximum dates available for
    reservations.

    The minimum date is today's date, and the maximum date is the last day of
    two months from today's date.
    """
    min_date = datetime.today().date()
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


def get_interval_options(intervals, min_date, reservation_date, table_options, check_availability):
    # print('* get_interval_options()')
    time_now_obj = datetime.now()
    interval_options = []
    
    for interval_kay, details in intervals.items():
        interval_kay_obj = datetime.combine(min_date, datetime.strptime(interval_kay, "%H:%M").time())
        # print(f"{time_now_obj=}, {interval_kay_obj=}")
        
        if reservation_date == min_date:
            # print(f'{reservation_date=}, {min_date=}')
            if time_now_obj < interval_kay_obj:
                available, available_intervals = check_availability(interval_kay, intervals, table_options, 12)
                if available_intervals == 12:
                    interval_options.append([interval_kay, f''])
                elif available_intervals > 8:
                    interval_options.append([interval_kay, f' - dostupno {available_intervals * 15} minuta'])
        else:
            available, available_intervals = check_availability(interval_kay, intervals, table_options, 12)
            if available_intervals == 12:
                interval_options.append([interval_kay, f''])
            elif available_intervals > 8:
                interval_options.append([interval_kay, f' - dostupno {available_intervals * 15} minuta'])
    
    return interval_options
    



def is_valid_user_input(user_inputs):
    if not user_inputs[0]:
        flash('Unesite email', 'danger')
        return False
    if not user_inputs[1]:
        flash('Unesite svoje Ime', 'danger')
        return False
    if not user_inputs[2]:
        flash('Unesite svoje Prezime', 'danger')
        return False
    if not user_inputs[3]:
        flash('Unesite broj telefona', 'danger')
        return False
    return True

def add_user_to_db(user_inputs):
    valid_inputs = is_valid_user_input(user_inputs)
    if valid_inputs:
        user = User.query.filter_by(email=user_inputs[0]).first()
        if user:
            flash('Korisnik sa tim email adresom vec postoji', 'danger')
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


def send_email(user, new_reservation):
    subject = f'Potvrda rezervacije - {new_reservation.reservation_number}'
    recipients = [user.email]
    cc = [] #! staviti mejl administratora
    body = f'Rezervacij {new_reservation.reservation_number} je uspesno kreirana na ime {user.name}. Uplaćena vredost od {new_reservation.amount} eura će biti umanjena od vrednosti računa.'
    message = Message(subject, recipients=recipients, cc=cc)
    message.html = body
    
    try:
        mail.send(message)
        flash('Mejl je uspesno poslat', 'success')
    except Exception as e:
        flash('Greska prilikom slanja mejla: ' + str(e), 'danger')