from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

from datetime import date
from datetime import datetime

from sentinelsat import SentinelAPI, read_geojson, geojson_to_wkt



# Declaring application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'fc191a6dbce62114c5c47480'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///agriculture.db'

# # Declaring Database
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.login_message_category = "danger"

from agriculture import routes
