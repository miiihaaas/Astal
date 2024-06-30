
from datetime import datetime, timedelta
from flask import flash, json
from astal import db
from astal.models import Calendar, Settings


def create_working_intervals(reservation_date):
    settings = Settings.query.first()
    reservation_date_obj = datetime.strptime(reservation_date, '%Y-%m-%d').date()
    reservation_month = reservation_date_obj.month
    if reservation_month < 10 and reservation_month > 4:
        start_hour = int(settings.summer_reservation_start_time.split(":")[0])
        end_hour = int(settings.summer_reservation_end_time.split(":")[0])
    else:
        start_hour = int(settings.winter_reservation_start_time.split(":")[0])
        end_hour = int(settings.winter_reservation_end_time.split(":")[0])
    avalable_tables_2 = settings.default_number_of_tables_2
    avalable_tables_4 = settings.default_number_of_tables_4
    intervals = {}
    for hour in range(0, 24):
        for minute in [0, 15, 30, 45]:
            if hour < start_hour:
                start_time = f"{hour:02d}:{minute:02d}"
                ending_minute = (minute + 15) % 60
                ending_hour = hour + (minute + 15) // 60
                end_time = f"{ending_hour:02d}:{ending_minute:02d}"
                intervals[start_time] = {
                    "start_time": start_time,
                    "end_time": end_time,
                    "available_tables_2": 0,
                    "available_tables_4": 0,
                    "reservations": [],
                    "booked_tables_2": 0, #! podrazumevana vrednost je nula jer za novi dan niko nije rezervisao još uvek sto
                    "booked_tables_4": 0, #! podrazumevana vrednost je nula jer za novi dan niko nije rezervisao još uvek sto
                    "free_tables_2": 0, #! podrazumevana vrednost je nula jer nije počelo radno vreme
                    "free_tables_4": 0 #! podrazumevana vrednost je nula jer nije počelo radno vreme
                }
            else:
                start_time = f"{hour:02d}:{minute:02d}"
                ending_minute = (minute + 15) % 60
                ending_hour = hour + (minute + 15) // 60
                end_time = f"{ending_hour:02d}:{ending_minute:02d}"
                intervals[start_time] = {
                    "start_time": start_time,
                    "end_time": end_time,
                    "available_tables_2": avalable_tables_2,
                    "available_tables_4": avalable_tables_4,
                    "reservations": [],
                    "booked_tables_2": 0, #! podrazumevana vrednost je nula jer za novi dan niko nije rezervisao još uvek sto
                    "booked_tables_4": 0, #! podrazumevana vrednost je nula jer za novi dan niko nije rezervisao još uvek sto
                    "free_tables_2": avalable_tables_2,
                    "free_tables_4": avalable_tables_4 
                }
    return intervals


def define_working_hours(reservation_date):
    new_intervals = create_working_intervals(reservation_date)
    new_resevations = Calendar(date=datetime.strptime(reservation_date, '%Y-%m-%d').date(), intervals=json.dumps(new_intervals))
    return new_resevations


def cancel_reservation(reservation, updated_intervals):
    for interval, details in updated_intervals.items():
        if len(details['reservations']):
            for reservation_details in details['reservations']:
                if reservation_details['reservation_id'] == reservation.id:
                    details['reservations'].remove(reservation_details)
                    details['booked_tables_2'] -= reservation_details['reserved_tables_2']
                    details['free_tables_2'] += reservation_details['reserved_tables_2']
                    details['booked_tables_4'] -= reservation_details['reserved_tables_4']
                    details['free_tables_4'] += reservation_details['reserved_tables_4']
    updated_intervals = updated_intervals
    reservation.status = 'cancelled'
    db.session.commit()
    return updated_intervals


def confirm_reservation(reservation):
    reservation.status = 'confirmed'
    db.session.commit()


def finish_reservation(reservation, updated_intervals):
    _, next_interval = calculate_next_interval()

    # Formatiranje sledećeg intervala u HH:MM format
    next_interval_str = next_interval.strftime("%H:%M")
    print(f'{next_interval=}')
    print(f'{next_interval_str=}')
    
    for interval, details in updated_intervals.items():
        interval_obj = datetime.strptime(interval, "%H:%M")
        interval_obj = next_interval.replace(hour=interval_obj.hour, minute=interval_obj.minute, second=0, microsecond=0)
        if next_interval <= interval_obj and len(details['reservations']):
            for reservation_details in details['reservations']:
                if reservation_details['reservation_id'] == reservation.id:
                    details['reservations'].remove(reservation_details)
                    details['booked_tables_2'] -= reservation_details['reserved_tables_2']
                    details['free_tables_2'] += reservation_details['reserved_tables_2']
                    details['booked_tables_4'] -= reservation_details['reserved_tables_4']
                    details['free_tables_4'] += reservation_details['reserved_tables_4']
    updated_intervals = updated_intervals
    reservation.end_time = next_interval_str
    reservation.status = 'finished'
    db.session.commit()
    return updated_intervals


def extend_reservation(reservation, updated_intervals):
    # print(f'{reservation.end_time=}')
    reservation_end_time = datetime.strptime(reservation.end_time, "%H:%M")
    next_interval_start, next_interval_end = calculate_next_interval(reservation_end_time)
    
    #! u prvom intervalu se traži id rezervacije odakle se dobjaju vrednosti za rezervisane stolove
    first_interval = updated_intervals[reservation.start_time]
    for reservation_details in first_interval['reservations']:
        if reservation_details['reservation_id'] == reservation.id:
            reserved_tables_2 = reservation_details['reserved_tables_2']
            reserved_tables_4 = reservation_details['reserved_tables_4']
            print(f'* {reserved_tables_2=}')
            print(f'* {reserved_tables_4=}')

    
    for interval, details in updated_intervals.items():
        if next_interval_start.strftime("%H:%M") == interval:
            if reserved_tables_2 < details['free_tables_2'] and reserved_tables_4 < details['free_tables_4']:
                details['reservations'].append({
                    "reservation_id": reservation.id,
                    "user_id": reservation.user_id,
                    "reserved_tables_2": reserved_tables_2, 
                    "reserved_tables_4": reserved_tables_4
                })
                details['free_tables_2'] -= reserved_tables_2
                details['free_tables_4'] -= reserved_tables_4
                details['booked_tables_2'] += reserved_tables_2
                details['booked_tables_4'] += reserved_tables_4
                
                reservation.end_time = next_interval_end.strftime("%H:%M")
                db.session.commit()
                flash(f'Vreme za rezervaciju {reservation.reservation_number} je uspešno produženo do {reservation.end_time}.', 'success')
            else:
                flash(f'Nema dovoljno stolova da bi se produžila rezervacija {reservation.reservation_number}', 'danger')

def calculate_next_interval(last_interval_obj=None):
    '''
    Funkcija za racunanje sledeceg intervala
    ako je unet interval, onda se racuna vreme u odnosu na taj interval
    ako nije unet interval, onda se racuna vreme u odnosu na trenutno vremeß
    '''
    if last_interval_obj:
        next_interval_start = last_interval_obj
    else:
        next_interval_start = (datetime.now() + timedelta(minutes=((15 - datetime.now().minute % 15) % 15 or 15))).replace(second=0, microsecond=0) # trenutno vreme zaouruženo na 15 minuta
    # Računanje sledećeg intervala
    minutes = (next_interval_start.minute // 15 + 1) * 15
    if minutes == 60:
        next_interval_end = (next_interval_start + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
    else:
        next_interval_end = next_interval_start.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=minutes)
    return next_interval_start, next_interval_end