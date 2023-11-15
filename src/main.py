from app import app, db
from app.models import User, Sample, Batch, Location, Result1, Mykrobe, Project, Sample_project


@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Sample': Sample, 'Batch': Batch, 'Location': Location, 'Result1': Result1, 'Mykrobe': Mykrobe, 'Sample_project': Sample_project, 'Project': Project}

if __name__ == "__main__":
    # this db.create_all() might just be needed for sqlite
    # i think it's a one time thing, only needs to be done first time
    db.create_all()
    app.run(debug=True)

