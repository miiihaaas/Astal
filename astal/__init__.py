import os
from dotenv import load_dotenv
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from celery import Celery




load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
#kod ispod treba da reši problem Internal Server Error - komunikacija sa serverom
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['FLASK_APP'] = 'run.py'

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER') #dodati u .env: 'mail.putninalozi.online'
app.config['MAIL_PORT'] = os.getenv('MAIL_PORT') #dodati u .env: 465
app.config['MAIL_USE_TLS'] = True #! bilo je False
app.config['MAIL_USE_SSL'] = False #! bilo je True
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER') # https://www.youtube.com/watch?v=IolxqkL7cD8&ab_channel=CoreySchafer
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS') # https://www.youtube.com/watch?v=IolxqkL7cD8&ab_channel=CoreySchafer -- za 2 step verification: https://support.google.com/accounts/answer/185833
app.config['MAIL_DEFAULT_SENDER'] = ('Astal_dev', 'miiihaaas@gmail.com')
mail = Mail(app)


# Celery konfiguracija
app.config['CELERY_BROKER_URL'] = 'amqp://guest:guest@localhost:5672//'
app.config['CELERY_RESULT_BACKEND'] = 'rpc://'
app.config['BROKER_HEARTBEAT'] = 10
app.config['BROKER_CONNECTION_TIMEOUT'] = 20
app.config['CELERY_TASK_ACKS_LATE'] = True  # Dodato da omogući kasno potvrđivanje
app.config['CELERY_BROKER_CONNECTION_MAX_RETRIES'] = 3  # Maksimalni broj pokušaja ponovnog povezivanja
app.config['CELERY_BROKER_HEARTBEAT'] = 30  # Vremenski interval između heartbeat poruka
app.config['CELERY_BROKER_CONNECTION_TIMEOUT'] = 30  # Vremenski interval za timeout veze
app.config['CELERY_TASK_SERIALIZER'] = 'json'
app.config['CELERY_RESULT_SERIALIZER'] = 'json'
app.config['CELERY_ACCEPT_CONTENT'] = ['json']
app.config['CELERY_TIMEZONE'] = 'Europe/Belgrade'
app.config['CELERY_ENABLE_UTC'] = True


def make_celery(app):
    celery = Celery(
        app.import_name,
        broker=app.config['CELERY_BROKER_URL'],
        backend=app.config['CELERY_RESULT_BACKEND'],
        include=['astal.main.routes', 'astal.admin.routes', 'astal.main.functions', 'astal.admin.functions']
    )
    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery

celery = make_celery(app)

from astal.main.routes import main
from astal.admin.routes import admin

app.register_blueprint(main)
app.register_blueprint(admin)


# Ovde importujemo modele kako bi se inicirala baza podataka
from astal.models import User, Reservation, Calendar

# Inicijalizacija baze podataka
with app.app_context():
    db.create_all()