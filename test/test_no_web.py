import os
from app import db
import app


def create_it():
    db.create_all()


def wipe_it_and_create_it():
    # putting this assertion here to stop me from wiping the non-test database
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    assert SQLALCHEMY_DATABASE_URI.split('/')[-1].startswith('test')
    #app.app.app_context().push()
    # db.session.remove()
    db.drop_all()
    db.create_all()


wipe_it_and_create_it()
# create_it()