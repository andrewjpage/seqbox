from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate


app = Flask(__name__) # Create a Flask app instance
app.config.from_object(Config)
 # Load ALL uppercase variables
 # from Python module 'config.py' into 'app.config'
Bootstrap(app)
db = SQLAlchemy(app) # Initialize the Flask-SQLAlchemy extension instance
# see here https://blog.miguelgrinberg.com/post/how-to-add-flask-migrate-to-an-existing-project
migrate = Migrate(app, db)
login = LoginManager(app)
login.login_view = 'login'

from app import routes, models
