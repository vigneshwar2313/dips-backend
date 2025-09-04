from flask import Flask
from app.routes import bookings, services, staff, users
from app.db.schema import init_db
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

front_end_urls = os.getenv('FRONT_END_URLS', '').split(',')

def create_app():
    app = Flask(__name__)
    CORS(app, origins=front_end_urls)

    init_db()

    app.register_blueprint(bookings.bookings_bp, url_prefix="/bookings")
    app.register_blueprint(services.services_bp, url_prefix="/services")
    app.register_blueprint(staff.staff_bp, url_prefix="/staff")
    app.register_blueprint(users.users_bp, url_prefix="/users")

    return app
