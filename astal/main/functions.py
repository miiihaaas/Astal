
import calendar
from datetime import datetime, timedelta

from flask import flash, redirect, url_for
from astal.models import User
from astal import db


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
    Calculates the number of tables required for a given number of people.

    The calculation is based on the following rules:

    - 1-4 person requires 1 table
    - 5-6 people require 2 tables
    - 7-8 people require 3 tables
    - 9-10 people require 4 tables
    - ...

    The function will return the minimum number of tables required to accommodate
    the given number of people.

    :param number_of_people: The number of people to be seated
    :return: The minimum number of tables required
    """
    for i in range(1, 16):  # 1 to 15 tables
        if number_of_people < (i * 2 + 3):  # adjust the condition to fit your requirements
            return i
    return 15

def check_availability(start_time, intervals, required_tables, num_intervals):
    start_time_found = False
    available_intervals = 0

    for interval, details in intervals.items():
        if interval == start_time:
            start_time_found = True
        if start_time_found:
            if details["free_tables"] >= required_tables:
                available_intervals += 1
            else:
                return False, available_intervals
            if available_intervals == num_intervals:
                return True, available_intervals
    return False, available_intervals


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


def book_tables(start_time, intervals, reservation_id, user_id, reserved_tables, num_intervals):
    start_time_found = False
    intervals_booked = 0

    for interval, details in intervals.items():
        if interval == start_time:
            start_time_found = True
        if start_time_found and details["free_tables"] >= reserved_tables:
            if intervals_booked < num_intervals:
                details["reservations"].append({
                    "reservation_id": reservation_id,
                    "user_id": user_id,
                    "reserved_tables": reserved_tables
                })
                details["booked_tables"] += reserved_tables
                details["free_tables"] -= reserved_tables
                intervals_booked += 1
            else:
                break
    return intervals