from datetime import datetime
from astal.admin.functions import cancel_reservation, confirm_reservation, define_working_hours, extend_reservation, finish_reservation
from astal import db
from astal.models import Calendar, Reservation, Settings
from flask import Blueprint, flash, json, redirect, render_template, request, jsonify, url_for


admin = Blueprint('admin', __name__)


@admin.route('/reservations', methods=['GET', 'POST'])
def reservations():
    # if request.method == 'GET':
    #     selected_date = request.form.get('reservation_date')
    # selected_date = datetime.today().date()
    # print(f'{selected_date=}')
    if request.method == 'POST':
        print('post')
        selected_date = request.form.get('reservation_date')
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    else:
        selected_date = request.args.get('selected_date')
        if not selected_date:
            selected_date = datetime.today().strftime('%Y-%m-%d')
        else:
            selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    reservations = Reservation.query.filter_by(reservation_date=selected_date).all()
    return render_template('reservations.html', reservations=reservations, selected_date=selected_date)


@admin.route('/edit_reservation', methods=['GET', 'POST'])
def edit_reservation():
    action = request.form.get('action')
    reservation = Reservation.query.get(request.form.get('reservation_id'))
    reservations_ = Calendar.query.filter_by(date=reservation.reservation_date).first()
    intervals = json.loads(reservations_.intervals)
    updated_intervals = intervals
    print(f'{reservation=}')
    print(f'{action=}')
    if action == 'confirm':
        print('pritisnuto je confirm')
        print(f"{request.form=}")
        confirm_reservation(reservation)
    elif action == 'cancel':
        print('pritisnuto je cancel')
        print(f"{request.form=}")
        updated_intervals = cancel_reservation(reservation, updated_intervals)
    elif action == 'finish':
        print('pritisnuto je finish')
        print(f"{request.form=}")
        updated_intervals = finish_reservation(reservation, updated_intervals)
    elif action == 'extend':
        print('pritisnuto je extend')
        print(f"{request.form=}")
        extend_reservation(reservation, updated_intervals)
    elif action == 'shorten':
        print('pritisnuto je shorten')
        print(f"{request.form=}")
    else:
        print('Pritisnuto je neko drugo dutme')
    reservations_.intervals = json.dumps(updated_intervals)
    db.session.commit()
    return redirect(url_for('admin.reservations'))

@admin.route('/calendar', methods=['GET', 'POST'])
def calendar():
    settings = Settings.query.first()
    # selected_date = datetime.today().date()
    if request.method == 'POST':
        selected_date = request.form.get('reservation_date')
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    else:
        selected_date = request.args.get('selected_date', datetime.today().strftime('%Y-%m-%d'))
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    reservations = Reservation.query.filter_by(reservation_date=selected_date).all()
    try:
        intervals = json.loads(Calendar.query.filter_by(date=selected_date).first().intervals)
    except:
        intervals = None
        # print(f'nije kreiran datum {selected_date=}')
    if not intervals:
        new_reservations = define_working_hours(settings, selected_date.strftime('%Y-%m-%d'))
        db.session.add(new_reservations)
        db.session.commit()
        intervals = json.loads(Calendar.query.filter_by(date=selected_date).first().intervals)
    # print(f'{intervals=}')
    table = []
    for interval, details in intervals.items():
        table.append({
            'interval': interval,
            'available_tables': details['available_tables'],
            'booked_tables': details['booked_tables'],
            'free_tables': details['free_tables'],
        })
    # print(f'{table=}')
    return render_template('calendar.html', 
                            reservations=reservations, 
                            selected_date=selected_date, 
                            table=table)


@admin.route('/update_tables', methods=['GET', 'POST'])
def update_tables():
    selected_date = request.form.get('reservation_date')
    interval_to_update = request.form.get('interval')
    available_tables = request.form.get('available_tables')
    # print(f'{selected_date=}, {interval_to_update=}, {available_tables=}')
    reservations = Calendar.query.filter_by(date=selected_date).first()
    intervals = json.loads(reservations.intervals)
    # print(f'{intervals=}')
    updated_intervals = intervals
    for interval, details in updated_intervals.items():
        if interval == interval_to_update:
            free_tables = int(available_tables) - details['booked_tables']
            details['available_tables'] = available_tables
            details['free_tables'] = free_tables
    # print(f'{updated_intervals=}')
    reservations.intervals = json.dumps(updated_intervals)
    db.session.commit()
    table = []
    for interval, details in intervals.items():
        table.append({
            'interval': interval,
            'available_tables': details['available_tables'],
            'booked_tables': details['booked_tables'],
            'free_tables': details['free_tables'],
        })
    flash(f'Uspesno ste promenili broj stolova za datum {selected_date} i interval {interval_to_update}', 'success')
    # return render_template('calendar.html', 
    #                         reservations=reservations, 
    #                         selected_date=selected_date,
    #                         table=table)
    return jsonify(success=True)


# @admin.route('/calendar', methods=['GET', 'POST'])
# def calendar():
#     selected_date = datetime.today().date()
    
#     if request.method == 'POST':
#         if 'reservation_date' in request.form and 'interval' in request.form:
#             # Logika za ažuriranje broja stolova
#             selected_date = request.form.get('reservation_date')
#             interval_to_update = request.form.get('interval')
#             available_tables = request.form.get('available_tables')
#             print(f'{selected_date=}, {interval_to_update=}, {available_tables=}')
            
#             reservations = Calendar.query.filter_by(date=selected_date).first()
#             intervals = json.loads(reservations.intervals)
#             print(f'{intervals=}')
            
#             for interval, details in intervals.items():
#                 if interval == interval_to_update:
#                     free_tables = int(available_tables) - details['booked_tables']
#                     details['available_tables'] = available_tables
#                     details['free_tables'] = free_tables
#             print(f'{intervals=}')
            
#             reservations.intervals = json.dumps(intervals)
#             db.session.commit()
#             flash(f'Uspesno ste promenili broj stolova za datum {selected_date} i interval {interval_to_update}', 'success')
#             return jsonify(success=True)
        
#         # Logika za promenu datuma rezervacije
#         selected_date = request.form.get('reservation_date')
#         selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    
#     reservations = Reservation.query.filter_by(reservation_date=selected_date).all()
    
#     try:
#         intervals = json.loads(Calendar.query.filter_by(date=selected_date).first().intervals)
#     except:
#         intervals = None
#         print(f'nije kreiran datum {selected_date=}')
    
#     if not intervals:
#         new_reservations = define_working_hours(0, 24, 10, selected_date.strftime('%Y-%m-%d'))
#         db.session.add(new_reservations)
#         db.session.commit()
#         intervals = json.loads(Calendar.query.filter_by(date=selected_date).first().intervals)
    
#     table = []
#     for interval, details in intervals.items():
#         table.append({
#             'interval': interval,
#             'available_tables': details['available_tables'],
#             'booked_tables': details['booked_tables'],
#             'free_tables': details['free_tables'],
#         })
    
#     print(f'{table=}')
#     return render_template('calendar.html', 
#                             reservations=reservations, 
#                             selected_date=selected_date, 
#                             table=table)