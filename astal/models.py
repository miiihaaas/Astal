from astal import app, db, login_manager
from flask_login import UserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer


@login_manager.user_loader
def load_user(user_id):
    print('ušao sam u funkciju load_user')
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(20), unique=False, nullable=False)
    surname = db.Column(db.String(20), unique=False, nullable=False)
    password = db.Column(db.String(60), nullable=True)
    phone = db.Column(db.String(20), unique=False, nullable=False)
    reservations = db.relationship('Reservation', backref='user', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.name}', '{self.surname}', '{self.email}')"


class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservation_number = db.Column(db.String(12), nullable=False) #! 20240519-001
    reservation_date = db.Column(db.Date, nullable=False)
    number_of_people = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    start_time = db.Column(db.String(20), nullable=False)
    end_time = db.Column(db.String(20), nullable=False)
    note = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    status = db.Column(db.String(20), nullable=False, default='pending') #! pending, confirmed, canceled, finished

    def __repr__(self):
        return f"Reservation('{self.reservation_date}', '{self.number_of_people}', '{self.amount}')"
    

class Calendar(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    intervals = db.Column(db.JSON, nullable=False)

    def __repr__(self):
        return f"Calendar('{self.date}', '{self.intervals}')"


class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reservation_coast_per_person = db.Column(db.Float, nullable=False)
    default_number_of_tables_2 = db.Column(db.Integer, nullable=False)
    default_number_of_tables_4 = db.Column(db.Integer, nullable=False)
    summer_season_start_month = db.Column(db.Integer, nullable=False) #! 2024-05-01 ---- napraviti da se godin dinamički menja
    winter_season_start_month = db.Column(db.Integer, nullable=False) #! 2024-10-01 ---- napraviti da se godin dinamički menja
    summer_reservation_start_time = db.Column(db.String(5), nullable=False) #! "00:00"
    summer_reservation_end_time = db.Column(db.String(5), nullable=False) #! "20:30"
    winter_reservation_start_time = db.Column(db.String(5), nullable=False) #! "00:00"
    winter_reservation_end_time = db.Column(db.String(5), nullable=False) #! "20:30"

    

with app.app_context():
    print('models: checkopint -> posle ovog koda treba da se inicira db!!')
    db.create_all()