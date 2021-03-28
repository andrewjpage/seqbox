import datetime
from app import app, db
from app.models import User, Sample, Post, Batch, Location, Result1, Mykrobe, Study, Sample_study

sample = Sample(id_sample=2, num_reads=1,
                        date_time=datetime.datetime.utcnow(), organism='Salmonella',
                        location='blah', batch=None,
                        path_r1='/oath1', path_r2='/path2',
                        result1=None, mykrobe=None)

print(sample)
#save the model to the database
db.session.add(sample)
db.session.commit()
