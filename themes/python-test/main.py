from __init__ import app, db
from __init__.models import User, Post


@app.shell_context_processor
def make_shell_context():
    return {'db' : db, 'User':User, 'Post' : Post}