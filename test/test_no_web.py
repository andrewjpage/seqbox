#!/usr/bin/env python3
import os
import sys
sys.path.append('./src/')
from app import db
import app

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
db = SQLAlchemy(app)

def create_it():
    db.create_all()

def wipe_it_and_create_it():
    # putting this assertion here to stop me from wiping the non-test database
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    assert SQLALCHEMY_DATABASE_URI.split('/')[3].startswith('test')
    #app.app.app_context().push()
    # db.session.remove()
    with app.app_context():
        db.drop_all()
        db.create_all()


wipe_it_and_create_it()
# create_it()
