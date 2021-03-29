
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    """[Configuration file]
    """

    # Flask-SQLAlchemy: Initialize
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-will-never-guess'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///pa_seqbox_v2_test.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False







