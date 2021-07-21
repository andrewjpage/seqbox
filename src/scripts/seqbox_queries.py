import os
import argparse
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from app.models import Sample, Project, SampleSource, ReadSet, ReadSetIllumina, ReadSetNanopore, RawSequencingBatch,\
    Extraction, RawSequencing, RawSequencingNanopore, RawSequencingIllumina, TilingPcr, Groups, CovidConfirmatoryPcr, \
    ReadSetBatch, PcrResult, PcrAssay, ArticCovidResult, PangolinResult


def get_nanopore_fastq_path(args, Session, data_dir):
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


def get_sample_barcode_batch(args, Session):
    pass
    # s = Session()
    # sample_barcode_batch = s.query(ReadSetNanopore, ReadSet.readset_identifier, Sample.sample_identifier,
    #                                ReadSetBatch.name) \
    #     .join(ReadSet) \
    #     .join(ReadSetBatch) \
    #     .join(RawSequencing) \
    #     .join(Extraction) \
    #     .join(Sample).all()
    # sample_barcode_batch = s.query(ReadSetNanopore, ReadSet.readset_identifier, ReadSetBatch.name) \
    #     .join(ReadSet) \
    #     .join(ReadSetBatch, ReadSet.readset_batch_id).all()
        # .join(RawSequencing) \
        # .join(Extraction) \
        # .join(Sample).all()
    # sqlalchemy version not working, use this sql instead.
    """
    select group_name, rs.readset_identifier, s.sample_identifier, rsb.name, rsn.barcode from read_set_nanopore rsn
    join read_set rs on rsn.readset_id = rs.id
    join read_set_batch rsb on rs.readset_batch_id = rsb.id
    join raw_sequencing r on rs.raw_sequencing_id = r.id
    join extraction e on r.extraction_id = e.id
    join sample s on e.sample_id = s.id
    join sample_source ss on s.sample_source_id = ss.id
    join sample_source_project ssp on ss.id = ssp.sample_source_id
    join project p on ssp.project_id = p.id
    join groups g on p.groups_id = g.id
    where rsb.name = '20201126_1403_MC-110370_0_FAO22951_ce2194d3'
    and rsn.barcode = 'barcode13';
    """
    # for x in sample_barcode_batch:
    #     print(x)


def run_command(args):
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    # from here https://stackoverflow.com/questions/43459182/proper-sqlalchemy-use-in-flask
    engine = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URI, echo=True)
    Session = sessionmaker(bind=engine)
    if args.command == 'get_nanopore_fastq_path':
        data_dir = {'mlw-gpu1': '/home/phil/data/seqbox'}
        get_nanopore_fastq_path(args, Session, data_dir)
    if args.command == 'get_sample_barcode_batch':
        get_sample_barcode_batch(args, Session)
    engine.dispose()


def main():
    parser = argparse.ArgumentParser(prog='seqbox_queries')
    subparsers = parser.add_subparsers(title='[sub-commands]', dest='command')
    parser_get_nanopore_fastq_path = subparsers.add_parser('get_nanopore_fastq_path',
                                                                help='get_nanopore_fastq_path')
    parser_get_sample_barcode_batch = subparsers.add_parser('get_sample_barcode_batch',
                                                           help='get_sample_barcode_batch')
    args = parser.parse_args()
    run_command(args)


if __name__ == '__main__':
    main()

