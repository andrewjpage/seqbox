import pprint
import datetime
from app import db
from app.models import Isolate, IlluminaReadSet


def add_isolate():
    isolate = Isolate(date_collected=datetime.datetime.utcnow(), species='Salmonella',
                            location='blah', isolate_identifier='PMQ124')
    print(isolate)
    #save the model to the database
    # use add_all([list, of, isolates]) to add multiples at the same time
    db.session.add(isolate)
    db.session.commit()

def add_isolate_and_irs():
    irs1 = IlluminaReadSet(read_set_filename='PMQ124_sequencing',
                                        path_r1="/path/to/PMQ124_sequencing_R1.fastq",
                                        path_r2="/path/to/PMQ124_sequencing_R2.fastq")
    irs2 = IlluminaReadSet(read_set_filename='PMQ124_sequencing',
                                        path_r1="/path/to/PMQ124_v2_sequencing_R1.fastq",
                                        path_r2="/path/to/PMQ124_v2_sequencing_R2.fastq")
    isolate = Isolate(date_collected=datetime.datetime.utcnow(), species='Salmonella',
                      location='blah', isolate_identifier='PMQ124')
    isolate.illumina_read_sets = [irs1, irs2]
    print(isolate.illumina_read_sets)
    db.session.add(isolate)
    db.session.commit()


def add_illumina_read_set():
    illumina_read_set = IlluminaReadSet(read_set_filename = 'PMQ124_sequencing',
                                        r1="/path/to/PMQ124_sequencing_R1.fastq",
                                        r2="/path/to/PMQ124_sequencing_R2.fastq")
    db.session.add(illumina_read_set)
    db.session.commit()
    return illumina_read_set



def query_isolates():
    # or can use db.session.query(Isolate)
    i = Isolate.query.all()
    for x in i:
        # pprint.pprint(x.__dict__)
        print(x.illumina_read_sets)

def query_irs():
    # or can use db.session.query(Isolate)
    i = IlluminaReadSet.query.all()
    pprint.pprint(i[0].isolate)
    # for x in i:
    #     print(x.__dict__)

def create_it():
    db.create_all()

# create_it()
# add_isolate()
query_isolates()
# add_and_link_irs()
# add_isolate_and_irs()
# query_irs()