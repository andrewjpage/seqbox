import pprint
import datetime
from app import db
from app.models import Sample, ReadSet, IlluminaReadSet, Mykrobe, NanoporeReadSet, Project, ReadSetBatch, SampleSource


def add_sample():
    sample1 = Sample(species='Salmonella', location='blah', sample_identifier='ASH001')
    sample2 = Sample(species='Salmonella', location='blah', sample_identifier='ASH002')
    # print(sample)
    #save the model to the database
    # use add_all([list, of, samples]) to add multiples at the same time
    db.session.add_all([sample1, sample2])
    db.session.commit()


def add_project():
    project1 = Project(project_details="a made up project")
    project2 = Project(project_details="a made up project")
    db.session.add_all([project1, project2])


def add_sample_samplesource_project_same_time():
    sample1 = Sample(species='Salmonella', sample_identifier='ASH004')
    sample2 = Sample(species='Salmonella', sample_identifier='ASH005')
    sample3 = Sample(species='Salmonella', sample_identifier='ASH006')
    samplesource1 = SampleSource(sample_source_identifier="patient1")
    samplesource2 = SampleSource(sample_source_identifier="patient2")
    project1 = Project(project_details="a made up project", group_name="BlahBlah")
    project2 = Project(project_details="a second made up project", group_name="BlahBlah")
    sample1.sample_source = samplesource1
    sample2.sample_source = samplesource2
    sample3.sample_source = samplesource1
    # patient1.samples.append(sample1)
    # patient2.samples.append(sample2)
    # patient2.samples.append(sample3)
    samplesource1.projects.append(project1)
    samplesource2.projects.append(project1)
    samplesource2.projects.append(project2)
    db.session.add_all([sample1, sample2, sample3])
    db.session.commit()


def add_sample_and_rs():
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
    sample = Sample(date_added=datetime.datetime.utcnow(), species='Salmonella',
                      location='blah', sample_identifier='ASH001')
    sample.read_sets = [rs1, rs2, rs3]
    # print(sample.illumina_read_sets)
    db.session.add(sample)
    db.session.commit()


def add_nanopore_read_set():
    nanopore_read_set = NanoporeReadSet(sample_id=1, read_set_filename='PMQ124_sequencing_nanopore',
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


def query_samples():
    # or can use db.session.query(Sample)
    i = Sample.query.all()
    for x in i:
        print(vars(x))
        # print(x.sample_identifier)
        # print(x.studies)
        # print(x.read_sets)
        # pprint.pprint(x.__dict__)
        # print([y for y in x.read_sets])


def query_rs():
    # or can use db.session.query(Sample)
    i = ReadSet.query.all()
    pprint.pprint(i)


def query_nrs():
    # or can use db.session.query(Sample)
    i = NanoporeReadSet.query.all()
    pprint.pprint(i)


def query_mykrobe():
    m = Mykrobe.query.all()
    for x in m:
        print(x)
        print(x.read_set_id)


def query_sample_reads_myk():
    a = db.session.query(Sample, ReadSet, Mykrobe)\
        .join(Sample, isouter=True)\
        .join(Mykrobe, isouter=True).distinct()

    pprint.pprint(a.all())
    # print()
    # pprint.pprint(b.all())
    # print()
    # pprint.pprint(c.all())


def join_nrs():
    a = db.session.query(Sample, NanoporeReadSet, Mykrobe)\
        .join(Sample)\
        .join(Mykrobe) \
        .all()
    pprint.pprint(a)


def query_project():
    # print()
    s = Project.query.all()
    for x in s:
        # print()
        print(x.samples)


def query_readsetbatch():
    m = ReadSetBatch.query.all()
    for x in m:
        print(x)
        print(x.read_sets)


def create_it():
    db.create_all()


create_it()
# add_sample()
# add_project()
# add_sample_project()
# add_sample_and_rs()
# add_sample_samplesource_project_same_time()
# add_nanopore_read_set()
# add_mykrobe()
# query_samples()
# query_rs()
# query_nrs()
# query_mykrobe()
# query_sample_reads_myk()
# join_nrs()
# query_project()
# query_readsetbatch()
