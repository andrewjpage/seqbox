import os

from app.models import Sample, Project, SampleSource, ReadSet, ReadSetIllumina, ReadSetNanopore, RawSequencingBatch,\
    Extraction, RawSequencing, RawSequencingNanopore, RawSequencingIllumina, TilingPcr, Groups, CovidConfirmatoryPcr, \
    ReadSetBatch, PcrResult, PcrAssay, ArticCovidResult, PangolinResult
import sqlalchemy
from sqlalchemy.orm import sessionmaker


def get_nanopore_fastq_path(Session, data_dir):
    s = Session()
    fastqs = s.query(ReadSetNanopore, ReadSet.readset_identifier, Groups.group_name, Sample.sample_identifier, ReadSet.data_storage_device)\
        .join(ReadSet) \
        .join(RawSequencing) \
        .join(Extraction) \
        .join(Sample) \
        .join(SampleSource) \
        .join(SampleSource.projects)\
        .join(Groups).all()
    # returns a "keyed tuple" https://stackoverflow.com/questions/31624530/return-sqlalchemy-results-as-dicts-instead-of-lists
    # so, we can convert to dict
    fastqs = [r._asdict() for r in fastqs]
    for x in fastqs:
        # print(x['data_storage_device'], x['group_name'], x['readset_identifier'], x['sample_identifier'])
        print(f"{data_dir[x['data_storage_device']]}/{x['group_name']}/{x['readset_identifier']}-{x['sample_identifier']}/{x['readset_identifier']}-{x['sample_identifier']}.fastq.gz")
        # print(x.__dict__)
        # print(x[2], x[1], x[3])
    s.close()


data_dir = {'mlw-gpu1': '/home/phil/data/seqbox'}

# from here https://stackoverflow.com/questions/43459182/proper-sqlalchemy-use-in-flask
SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
engine = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
Session = sessionmaker(bind=engine)

if __name__ == '__main__':
    get_nanopore_fastq_path(Session, data_dir)

engine.dispose()
