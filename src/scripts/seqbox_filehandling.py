import os
import sys
import yaml
import glob
import shutil
import argparse
from app import db
from app.models import ReadSetBatch
from seqbox_utils import read_in_as_dict, get_readset, get_nanopore_readset_from_batch_and_barcode, \
    basic_check_readset_fields


def read_in_config(config_inhandle):
    with open(config_inhandle) as fi:
        return yaml.safe_load(fi)


def get_group_name(extraction_from, readset):
    # check that extraction_from is one of the expected values
    assert extraction_from in {'whole_sample', 'cultured_isolate'}
    # get the project name, accounting for either extracts that are linked to samples, or extracts that are linked to
    # cultures. we can tell which of these we need from the readset_info['extraction_from'] field.
    projects = None
    if extraction_from == 'whole_sample':
        projects = readset.raw_sequencing.extraction.sample.sample_source.projects
    elif extraction_from == 'cultured_isolate':
        projects = readset.raw_sequencing.extraction.culture.sample.sample_source.projects
    group_names = [x.groups.group_name for x in projects]
    # a sample can only belong to one group, so this assertion should always be true.
    assert len(set(group_names)) == 1
    group_name = group_names[0]
    return group_name


def check_fastqs_exist(readset):
    if readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'nanopore':
        assert os.path.isfile(readset.readset_nanopore.path_fastq)
    elif readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'illumina':
        print(readset.readset_illumina.path_r1)
        assert os.path.isfile(readset.readset_illumina.path_r1)
        assert os.path.isfile(readset.readset_illumina.path_r2)


def get_sample_name(extraction_from, readset):
    sample_name = None
    # if the extraction is from whole sample, then we get the sample name by linking from extraction to sample directly.
    if extraction_from == 'whole_sample':
        sample_name = readset.raw_sequencing.extraction.sample.sample_identifier
    # if the extraction is from cultured isolate, then we get from extraction to sample via culture.
    elif extraction_from == 'cultured_isolate':
        sample_name = readset.raw_sequencing.extraction.culture.sample.sample_identifier
    return sample_name


def get_input_fastq_path(readset, args_nanopore_default, config, sample_name):
    # note - this code is quite fragile, will need to see what happens in reality and make changes accordingly.
    # if it's nanopore default, then we need to get the fastq from the nanopore readset batchname and the barcode
    if args_nanopore_default is True:
        input_fastq_path = glob.glob(os.path.join(config['sequencing_inbox'], readset.readset_batch.name, readset.readset_nanopore.barcode, "*.fastq.gz"))
        assert len(input_fastq_path) == 1
        return input_fastq_path[0]
    # otherwise, can either be illumina, or external nanopore (i.e. nanopore files named according to sample name)
    elif args_nanopore_default is False:
        # if it's illumina sequencing
        if readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'illumina':
            # if there is a Fastq dir within the batch dir, then it is probably an illumina run from our MiSeq
            # and therefore we need to account for the annoying illumina name format e.g. CQJ14G_S1_L001_R1_001.fastq.gz
            if os.path.isdir(os.path.join(config['sequencing_inbox'], readset.readset_batch.name, 'Fastq')):
                input_r1_path = glob.glob(os.path.join(config['sequencing_inbox'], readset.readset_batch.name, 'Fastq', f'{sample_name}*_R1_*.fastq.gz'))
                input_r2_path = glob.glob(os.path.join(config['sequencing_inbox'], readset.readset_batch.name, 'Fastq', f'{sample_name}*_R2_*.fastq.gz'))
            # if there is not, then they are probably external fastqs with more normal names e.g. CQJ14G_1.fastq.gz
            else:
                input_r1_path = glob.glob(os.path.join(config['sequencing_inbox'], readset.readset_batch.name, f'{sample_name}*_1.fastq.gz'))
                input_r2_path = glob.glob(os.path.join(config['sequencing_inbox'], readset.readset_batch.name, f'{sample_name}*_2.fastq.gz'))
            # check that the above found some files, and return the filenames if so
            assert len(input_r1_path) == 1
            assert len(input_r2_path) == 1
            return input_r1_path[0], input_r2_path[0]
        # if it's nanopore sequencing, then there will only be one fastq
        elif readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'nanopore':
            input_fastq_path = glob.glob(os.path.join(config['sequencing_inbox'], readset.readset_batch.name, f'{sample_name}*.fastq.gz'))
            assert len(input_fastq_path) == 1
            return input_fastq_path[0]


def add_readset_to_filestructure(readset, config, extraction_from, args_nanopore_default):
    '''
    1. Check that input files exist
    2. get readset_identifier-filename for this sample
    3. check that output dir exists (make it if not)
        a. will be /Users/flashton/Dropbox/non-project/test_seqbox_data/Core/[readset_identifier]-filename/
    4. copy the fastq to the output_dir - we copy rather than symlink because could be across volumes, as the dropbox
        will be Core, and the readset dir could be another group.
    5. copy the readset dir to the slow dir for that group.
    6. add the paths to the database.
    '''

    # data is going to be stored in a directory with the group name, so need to get the group name of this readset.
    # adding to the fast directory
    group_name = get_group_name(extraction_from, readset)
    group_dir = os.path.join(config['seqbox_directory_fast'], 'fast', group_name)
    if not os.path.isdir(group_dir):
        os.mkdir(group_dir)

    # going to name the linked file with the sample name and readset_identifier
    sample_name = get_sample_name(extraction_from, readset)

    readset_dir = os.path.join(group_dir, f"{readset.readset_identifier}-{sample_name}")
    if not os.path.isdir(readset_dir):
        os.mkdir(readset_dir)

    if readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'nanopore':
        # get_input_fastq_path() will return one fastq path if the sequencing type is nanopore, or two if it's illumina
        input_fastq_path = get_input_fastq_path(readset, args_nanopore_default, config, sample_name)
        output_readset_fastq_path = os.path.join(readset_dir, f"{readset.readset_identifier}-{sample_name}.fastq.gz")
        if os.path.isfile(output_readset_fastq_path):
            print(f"{output_readset_fastq_path} already exists. Exiting.")
            sys.exit()
        else:
            # doing a copy instead of a symlink because we're going to have the dropbox always be on the fast/Core,
            # but the output for non-Core samples will be e.g. fast/Salmonella, which is a different volume so we need
            # to copy.
            shutil.copy(input_fastq_path, output_readset_fastq_path)
    elif readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'illumina':
        # get_input_fastq_path() will return one fastq path if the sequencing type is nanopore, or two if it's illumina
        input_r1_path, input_r2_path = get_input_fastq_path(readset, args_nanopore_default, config, sample_name)
        output_readset_r1_fastq_path = os.path.join(readset_dir, f"{readset.readset_identifier}-{sample_name}_R1.fastq.gz")
        output_readset_r2_fastq_path = os.path.join(readset_dir, f"{readset.readset_identifier}-{sample_name}_R2.fastq.gz")
        assert os.path.isfile(output_readset_r2_fastq_path) is False
        # copy r1 and r2 to the readset dir
        # doing a copy instead of a symlink because we're going to have the dropbox always be on the fast/Core,
        # but the output for non-Core samples will be e.g. fast/Salmonella, which is a different volume so we need
        # to copy.
        shutil.copy(input_r1_path, output_readset_r1_fastq_path)
        shutil.copy(input_r2_path, output_readset_r2_fastq_path)
    print(f"Added readset to fast filestructure {readset.readset_identifier}-{sample_name} to {group_dir}")
    # copy the readset to the slow directory
    # make the slow dir group path and readset dir.
    slow_group_dir = os.path.join(config['seqbox_directory_fast'], 'slow', group_name)
    if not os.path.isdir(slow_group_dir):
        os.mkdir(slow_group_dir)
    slow_readset_dir = os.path.join(slow_group_dir, f"{readset.readset_identifier}-{sample_name}")
    # recursively copy the readset dir from the fast dir to the slow dir
    shutil.copytree(readset_dir, slow_readset_dir)
    print(f"Added readset to slow filestructure {readset.readset_identifier}-{sample_name} to {slow_group_dir}")
    print(f"Adding slow path to database for {readset.readset_identifier}-{sample_name}")
    if readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'nanopore':
        readset.readset_nanopore.fastq_path = os.path.join(slow_readset_dir, f"{readset.readset_identifier}-{sample_name}.fastq.gz")
    elif readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'illumina':
        readset.readset_illumina.path_r1 = os.path.join(slow_readset_dir, f"{readset.readset_identifier}-{sample_name}_R1.fastq.gz")
        readset.readset_illumina.path_r2 = os.path.join(slow_readset_dir, f"{readset.readset_identifier}-{sample_name}_R2.fastq.gz")
    db.session.commit()


def run_add_readset_to_filestructure(args):
    config = read_in_config(args.seqbox_config)
    all_readsets_info = read_in_as_dict(args.readsets_inhandle)
    for readset_info in all_readsets_info:
        if basic_check_readset_fields(readset_info) is False:
            continue
        # nanopore default means that the sequencing run is in the default nanopore file structure
        # i.e. batchname/barcodeXX/XX.fastq.gz
        if args.nanopore_default is True:
            readset_nanopore = get_nanopore_readset_from_batch_and_barcode(readset_info)
            if readset_nanopore is False:
                print(f"There is no readset for\n{readset_info}\nExiting.")
                sys.exit()
            else:
                add_readset_to_filestructure(readset_nanopore.readset, config, readset_info['extraction_from'],
                                             args.nanopore_default)
        elif args.nanopore_default is False:
            # if it's not nanopore default, can either be illumina, or a non-default nanopore. non-default nanopore
            # basically means that it is a nanopore dataset from another sequencing facility.
            # readset_tech is either readset_illumina or readset_nanopore
            readset_tech = get_readset(readset_info, args.covid)
            if readset_tech is False:
                print(f"There is no readset for\n{readset_info}\nExiting.")
                sys.exit()
            else:
                add_readset_to_filestructure(readset_tech.readset, config, readset_info['extraction_from'],
                                             args.nanopore_default)


def run_add_artic_consensus_to_filestructure(args):
    config = read_in_config(args.seqbox_config)
    '''
    1. get readset batch
    2. for each readset in batch, get:
        a. readset id
        b. sample_identifier
        c. group_name
    3. get all readset ids 
    '''
    rsb = ReadSetBatch.query.filter_by(name=args.readset_batch_name).all()
    assert len(rsb) == 1
    for rs in rsb[0].readsets:
        sample = rs.raw_sequencing.extraction.sample
        group_name = sample.sample_source.projects[0].groups.group_name
        target_dir = os.path.join(config['seqbox_directory'], group_name, f"{rs.readset_identifier}-{sample.sample_identifier}", "artic_pipeline")
        target_consensus = os.path.join(target_dir, f"{rs.readset_identifier}-{sample.sample_identifier}.artic.consensus.fasta")
        if not os.path.isfile(target_consensus):
            source_consensus = glob.glob(
                    f"{args.consensus_genomes_parent_dir}/{args.readset_batch_name}_{rs.readset_nanopore.barcode}.consensus.fasta")
            if len(source_consensus) == 1:
                if not os.path.isdir(target_dir):
                    os.mkdir(target_dir)
                #os.symlink(source_consensus[0], target_consensus)
                shutil.copy(source_consensus[0], target_consensus)
                print(f"Linked {source_consensus[0]} to {target_consensus}")
            elif len(source_consensus) == 0:
                print(f"No consensus genome at {args.consensus_genomes_parent_dir}/{args.readset_batch_name}_{rs.readset_nanopore.barcode}.consensus.fasta")
            elif len(source_consensus) > 1:
                print(f"More than one consensus genome at {args.consensus_genomes_parent_dir}/{args.readset_batch_name}_{rs.readset_nanopore.barcode}.consensus.fasta")

        target_bam = os.path.join(target_dir, f"{rs.readset_identifier}-{sample.sample_identifier}.artic.bam")
        if not os.path.isfile(target_bam):
            source_bam = glob.glob(
                    f"{args.consensus_genomes_parent_dir}/{args.readset_batch_name}_{rs.readset_nanopore.barcode}.primertrimmed.rg.sorted.bam")
            if len(source_bam) == 1:
                if not os.path.isdir(target_dir):
                    os.mkdir(target_dir)
                shutil.copy(source_bam[0], target_bam)
                #os.symlink(source_bam[0], target_bam)
                print(f"Linked {source_bam[0]} to {target_bam}")
            elif len(source_bam) == 0:
                print(f"No bam at {args.consensus_genomes_parent_dir}/{args.readset_batch_name}_{rs.readset_nanopore.barcode}.primertrimmed.rg.sorted.bam")
            elif len(source_bam) > 1:
                print(f"More than one bam at {args.consensus_genomes_parent_dir}/{args.readset_batch_name}_{rs.readset_nanopore.barcode}.primertrimmed.rg.sorted.bam")


def run_command(args):
    if args.command == 'add_readset_to_filestructure':
        run_add_readset_to_filestructure(args=args)
    if args.command == 'add_artic_consensus_to_filestructure':
        run_add_artic_consensus_to_filestructure(args=args)


def main():
    parser = argparse.ArgumentParser(prog='seqbox_filehandling')
    subparsers = parser.add_subparsers(title='[sub-commands]', dest='command')
    parser_add_readset_to_filestructure = subparsers.add_parser('add_readset_to_filestructure',
                                                                help='Take a csv file of samples and add links to the '
                                                                     'file structure')
    parser_add_readset_to_filestructure.add_argument('-i', dest='readsets_inhandle', help='A CSV file containing samples'
                                     , required=True)
    parser_add_readset_to_filestructure.add_argument('-c', dest='seqbox_config',
                                     help='The path to a seqbox_config file.', required=True)
    # this is needed because need to do the join through tiling pcr for covid samples.
    # should replace the query that is done here with a union query so don't need to do this.
    parser_add_readset_to_filestructure.add_argument('-s', dest='covid', action='store_true', default=False,
                                     help='Are these readsets SARS-CoV-2?')
    parser_add_readset_to_filestructure.add_argument('-n', dest='nanopore_default', action='store_true', default=False,
                                     help='Are the data for these readsets arranged in nanopore default format? I.e. by'
                                          'batch and the barcode?')

    parser_add_artic_consensus_to_filestructure = subparsers.add_parser('add_artic_consensus_to_filestructure',
                                                                help='Add artic consensus files to seqbox filestructure'
                                                                     ' for a sequencing batch, nanopore default format.')
    parser_add_artic_consensus_to_filestructure.add_argument('-b', dest='readset_batch_name',
                                                     help='the readset batch name', required=True)
    parser_add_artic_consensus_to_filestructure.add_argument('-c', dest='seqbox_config',
                                                     help='The path to a seqbox_config file.', required=True)
    parser_add_artic_consensus_to_filestructure.add_argument('-d', dest='consensus_genomes_parent_dir',
                                                             help='Absolute path to the artic pipeline results dir',
                                                             required=True)
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
    args = parser.parse_args()
    run_command(args)


if __name__ == '__main__':
    main()
