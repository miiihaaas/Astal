from datetime import datetime

from flask_login import current_user, login_user, logout_user
from flask import Blueprint, flash, json, redirect, render_template, request, jsonify, url_for
from astal.admin.functions import cancel_reservation, confirm_reservation, define_working_hours, extend_reservation, finish_reservation
from astal import db, bcrypt
from astal.models import Calendar, Reservation, Settings, User
from astal.admin.forms import LoginForm


admin = Blueprint('admin', __name__)


@admin.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    settings = Settings.query.first()
    print(f'current user: {current_user}')
    if current_user.is_authenticated:
        flash('Vec ste prijavljeni', 'info')
        return redirect(url_for('admin.reservations'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        print(f'user: {user}')
        print(f'password form hash: {bcrypt.generate_password_hash(form.password.data).decode("utf-8")}')
        print(f'password check: {bcrypt.check_password_hash(user.password, form.password.data)}')
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Dobro došli, {user.name}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('admin.reservations'))
        else:
            flash(f'Email ili lozinka nisu odgovarajući.', 'danger')
    return render_template('login.html', 
                            title=f'{settings.restaurant_name} - Prijavljivanje', 
                            form=form, 
                            legend='Prijavljivanje', 
                            settings=settings)


@admin.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home', language='mn'))

@admin.route('/reservations', methods=['GET', 'POST'])
def reservations():
    settings = Settings.query.first()
    if current_user.is_anonymous:
        flash('Nemate autorizaciju da pristupite ovoj stranici.', 'danger')
        return redirect(url_for('main.home'))
    if request.method == 'POST':
        print('post')
        selected_date = request.form.get('reservation_date')
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    else:
        selected_date = request.args.get('selected_date')
        if not selected_date:
            selected_date = datetime.today().strftime('%Y-%m-%d')
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').date() # Uvek konvertuj u date objekat
    
    print(f'{selected_date=}')
    print(f'{datetime.today().date()=}')
    
    if selected_date != datetime.today().date():
        show_column = False
    else:
        show_column = True
        
    #############################################################################################################################
    #############################################################################################################################
    #############################################################################################################################
    reservations = Reservation.query.filter_by(reservation_date=selected_date).all()
    #TODO KADA VREMENOM PROĐE DATUM ZA SVE REZERVACIJE KOJE NISU PLAĆENE AKTIVIRATI KOD ISPOD A KOD IZNAD ZAKOMENTARISATI --- 18/10/2024
    #! all_reservations = Reservation.query.filter_by(reservation_date=selected_date).all()
    #! reservations = [reservation for reservation in all_reservations if reservation.status != 'unpaid']
    #############################################################################################################################
    #############################################################################################################################
    #############################################################################################################################
    
    return render_template('reservations.html', 
                            reservations=reservations, 
                            selected_date=selected_date, 
                            show_column=show_column,
                            title=f'{settings.restaurant_name} - Lista rezervacija',
                            settings=settings)



@admin.route('/edit_reservation', methods=['GET', 'POST'])
def edit_reservation():
    if current_user.is_anonymous:
        flash('Nemate autorizaciju da pristupite ovoj stranici.', 'danger')
        return redirect(url_for('main.home'))
    action = request.form.get('action')
    reservation = Reservation.query.get(request.form.get('reservation_id'))
    reservations_ = Calendar.query.filter_by(date=reservation.reservation_date).first()
    intervals = json.loads(reservations_.intervals)
    updated_intervals = intervals
    print(f'{reservation=}')
    print(f'{action=}')
    if action == 'confirm':
        # print(f"{request.form=}")
        confirm_reservation(reservation)
        flash(f'Rezervacija {reservation.reservation_number} na ime {reservation.user.name} {reservation.user.surname} je uspešno potvrđena.', 'success')
    elif action == 'cancel':
        # print(f"{request.form=}")
        updated_intervals = cancel_reservation(reservation, updated_intervals)
        flash(f'Rezervacija {reservation.reservation_number} na ime {reservation.user.name} {reservation.user.surname} je uspešno otkazana.', 'danger')
    elif action == 'finish':
        # # print(f"{request.form=}")
        updated_intervals = finish_reservation(reservation, updated_intervals)
        flash(f'Rezervacija {reservation.reservation_number} na ime {reservation.user.name} {reservation.user.surname} je uspešno završena.', 'success')
    elif action == 'extend':
        # print(f"{request.form=}")
        extend_reservation(reservation, updated_intervals)
    else:
        print('Pritisnuto je neko drugo dutme')
    reservations_.intervals = json.dumps(updated_intervals)
    db.session.commit()
    return redirect(url_for('admin.reservations'))

@admin.route('/calendar', methods=['GET', 'POST'])
def calendar():
    if current_user.is_anonymous:
        flash('Nemate autorizaciju da pristupite ovoj stranici.', 'danger')
        return redirect(url_for('main.home'))
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
        new_reservations = define_working_hours(selected_date.strftime('%Y-%m-%d'))
        db.session.add(new_reservations)
        db.session.commit()
        intervals = json.loads(Calendar.query.filter_by(date=selected_date).first().intervals)
    # print(f'{intervals=}')
    table = []
    for interval, details in intervals.items():
        table.append({
            'interval': interval,
            'available_tables_2': details['available_tables_2'],
            'booked_tables_2': details['booked_tables_2'],
            'free_tables_2': details['free_tables_2'],
            'available_tables_4': details['available_tables_4'],
            'booked_tables_4': details['booked_tables_4'],
            'free_tables_4': details['free_tables_4'],
        })
    # print(f'{table=}')
    return render_template('calendar.html', 
                            reservations=reservations, 
                            selected_date=selected_date, 
                            table=table,
                            title=f'{settings.restaurant_name} - Dnevnik',
                            settings=settings)


@admin.route('/update_tables', methods=['GET', 'POST'])
def update_tables():
    if current_user.is_anonymous:
        flash('Nemate autorizaciju da pristupite ovoj stranici.', 'danger')
        return redirect(url_for('main.home'))
    
    selected_date = request.form.get('reservation_date')
    interval_to_update = request.form.get('interval')
    available_tables_2 = request.form.get('available_tables_2')
    available_tables_4 = request.form.get('available_tables_4')
    print(f'{selected_date=}, {interval_to_update=}, {available_tables_2=}, {available_tables_4=}')
    # print(f'{selected_date=}, {interval_to_update=}, {available_tables=}')
    reservations = Calendar.query.filter_by(date=selected_date).first()
    intervals = json.loads(reservations.intervals)
    # print(f'{intervals=}')
    updated_intervals = intervals
    for interval, details in updated_intervals.items():
        if interval == interval_to_update:
            free_tables_2 = int(available_tables_2) - details['booked_tables_2']
            details['available_tables_2'] = available_tables_2
            free_tables_4 = int(available_tables_4) - details['booked_tables_4']
            details['available_tables_4'] = available_tables_4
            details['free_tables_2'] = free_tables_2
            details['free_tables_4'] = free_tables_4
    # print(f'{updated_intervals=}')
    reservations.intervals = json.dumps(updated_intervals)
    db.session.commit()
    table = []
    for interval, details in intervals.items():
        table.append({
            'interval': interval,
            'available_tables_2': details['available_tables_2'],
            'available_tables_4': details['available_tables_4'],
            'booked_tables_2': details['booked_tables_2'],
            'booked_tables_4': details['booked_tables_4'],
            'free_tables_2': details['free_tables_2'],
            'free_tables_4': details['free_tables_4'],
        })
    flash(f'Uspešno ste promenili broj raspoloživih stolova za datum {selected_date} i za interval {interval_to_update}.', 'success')
    # return render_template('calendar.html', 
    #                         reservations=reservations, 
    #                         selected_date=selected_date,
    #                         table=table)
    return jsonify(success=True)

@admin.route('/reset_tables', methods=['POST'])
def reset_tables():
    if current_user.is_anonymous:
        flash('Nemate autorizaciju da pristupite ovoj stranici.', 'danger')
        return jsonify(success=False), 403
    data = request.get_json()
    selected_date = data.get('reservation_date')
    reservations = Calendar.query.filter_by(date=selected_date).first()
    if not reservations:
        flash('Nema rezervacija za izabrani datum.', 'warning')
        return jsonify(success=False)
    intervals = json.loads(reservations.intervals)
    for interval, details in intervals.items():
        details['available_tables_2'] = 0
        details['available_tables_4'] = 0
        details['free_tables_2'] = 0 - details['booked_tables_2']
        details['free_tables_4'] = 0 - details['booked_tables_4']
    reservations.intervals = json.dumps(intervals)
    db.session.commit()
    flash(f'Svi intervali su postavljeni na nulu za datum {selected_date}.', 'success')
    return jsonify(success=True)