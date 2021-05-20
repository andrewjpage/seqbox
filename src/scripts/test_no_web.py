import pprint
import datetime
from app import db
from app.models import Isolate, ReadSet, IlluminaReadSet, Mykrobe, NanoporeReadSet, Project, isolate_project, \
    ReadSetBatch


def add_isolate():
    isolate1 = Isolate(species='Salmonella', location='blah', isolate_identifier='ASH001')
    isolate2 = Isolate(species='Salmonella', location='blah', isolate_identifier='ASH002')
    # print(isolate)
    #save the model to the database
    # use add_all([list, of, isolates]) to add multiples at the same time
    db.session.add_all([isolate1, isolate2])
    db.session.commit()


def add_project():
    project1 = Project(project_details="a made up project")
    project2 = Project(project_details="a made up project")
    db.session.add_all([project1, project2])


def add_isolate_project():
    # isolate_project.insert().values(isolate_id=1, project_id=1)
    db.session.execute(isolate_project.insert(), params={"isolate_id": 1, "project_id": 1})
    db.session.execute(isolate_project.insert(), params={"isolate_id": 2, "project_id": 1})
    db.session.execute(isolate_project.insert(), params={"isolate_id": 1, "project_id": 2})
    db.session.commit()


def add_isolate_project_same_time():
    isolate1 = Isolate(species='Salmonella', location='blah', isolate_identifier='ASH001')
    isolate2 = Isolate(species='Salmonella', location='blah', isolate_identifier='ASH002')
    project1 = Project(project_details="a made up project")
    project2 = Project(project_details="a made up project")
    isolate1.studies.append(project1)
    isolate2.studies.append(project1)
    isolate2.studies.append(project2)
    db.session.add_all([isolate1, isolate2])
    db.session.commit()


def add_isolate_and_rs():
    rs1 = ReadSet(read_set_filename='ASH001_sequencing', type="illumina")
    rs2 = ReadSet(read_set_filename='ASH001_v2_sequencing', type="illumina")
    irs1 = IlluminaReadSet(read_set_id=1, path_r1="/path/to/ASH001_sequencing_1.fastq",
                           path_r2="/path/to/ASH001_sequencing_2.fastq")
    irs2 = IlluminaReadSet(read_set_id=2, path_r1="/path/to/ASH001_v2_sequencing_1.fastq",
                           path_r2="/path/to/ASH001_v2_sequencing_2.fastq")
    rs1.illumina_read_sets = [irs1]
    rs2.illumina_read_sets = [irs2]
    rs3 = ReadSet(read_set_filename="ASH001_nanop", type="nanopore")
    nrs1 = NanoporeReadSet(read_set_id=3, path_fastq="/path/to/ASH001_nanopore_sequencing.fastq")
    rs3.nanopore_read_sets = [nrs1]
    isolate = Isolate(date_added=datetime.datetime.utcnow(), species='Salmonella',
                      location='blah', isolate_identifier='ASH001')
    isolate.read_sets = [rs1, rs2, rs3]
    # print(isolate.illumina_read_sets)
    db.session.add(isolate)
    db.session.commit()


def add_nanopore_read_set():
    nanopore_read_set = NanoporeReadSet(isolate_id=1, read_set_filename='PMQ124_sequencing_nanopore',
                                        path_fast5="/path/to/PMQ124_sequencing.nanopore.fast5",
                                        path_fastq="/path/to/PMQ124_sequencing.nanopore.fastq")
    db.session.add(nanopore_read_set)
    db.session.commit()


def add_illumina_read_set():
    illumina_read_set = IlluminaReadSet(read_set_filename='PMQ124_sequencing',
                                        r1="/path/to/PMQ124_sequencing_R1.fastq",
                                        r2="/path/to/PMQ124_sequencing_R2.fastq")
    db.session.add(illumina_read_set)
    db.session.commit()
    # return nanopore_read_set


def add_mykrobe():
    myk = Mykrobe(read_set_id=1, species='Mtb_ill1', mykrobe_version="v0.8.0")
    db.session.add(myk)
    myk = Mykrobe(read_set_id=2, species='Mtb_ill2', mykrobe_version="v0.8.0")
    db.session.add(myk)
    myk = Mykrobe(read_set_id=3, species='Mtb_nanop', mykrobe_version="v0.8.0")
    db.session.add(myk)
    db.session.commit()


def query_isolates():
    # or can use db.session.query(Isolate)
    i = Isolate.query.all()
    for x in i:
        print(vars(x))
        # print(x.isolate_identifier)
        # print(x.studies)
        # print(x.read_sets)
        # pprint.pprint(x.__dict__)
        # print([y for y in x.read_sets])


def query_rs():
    # or can use db.session.query(Isolate)
    i = ReadSet.query.all()
    pprint.pprint(i)


def query_nrs():
    # or can use db.session.query(Isolate)
    i = NanoporeReadSet.query.all()
    pprint.pprint(i)


def query_mykrobe():
    m = Mykrobe.query.all()
    for x in m:
        print(x)
        print(x.read_set_id)


def query_isolate_reads_myk():
    a = db.session.query(Isolate, ReadSet, Mykrobe)\
        .join(Isolate, isouter=True)\
        .join(Mykrobe, isouter=True).distinct()

    pprint.pprint(a.all())
    # print()
    # pprint.pprint(b.all())
    # print()
    # pprint.pprint(c.all())


def join_nrs():
    a = db.session.query(Isolate, NanoporeReadSet, Mykrobe)\
        .join(Isolate)\
        .join(Mykrobe) \
        .all()
    pprint.pprint(a)


def query_project():
    # print()
    s = Project.query.all()
    for x in s:
        # print()
        print(x.isolates)


def query_readsetbatch():
    m = ReadSetBatch.query.all()
    for x in m:
        print(x)
        print(x.read_sets)


def create_it():
    db.create_all()


create_it()
# add_isolate()
# add_project()
# add_isolate_project()
# add_isolate_and_rs()
# add_isolate_project_same_time()
# add_nanopore_read_set()
# add_mykrobe()
# query_isolates()
# query_rs()
# query_nrs()
# query_mykrobe()
# query_isolate_reads_myk()
# join_nrs()
# query_project()
# query_readsetbatch()
