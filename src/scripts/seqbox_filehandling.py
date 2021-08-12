import os
import sys
import yaml
import glob
import argparse
from app.models import ReadSetBatch
from seqbox_utils import read_in_as_dict, get_readset, get_nanopore_readset_from_batch_and_barcode, \
    basic_check_readset_fields


def read_in_config(config_inhandle):
    with open(config_inhandle) as fi:
        return yaml.safe_load(fi)


def add_readset_to_filestructure(readset, config):
    '''
    1. Check that input files exist
    2. get readset_identifier-filename for this sample
    3. check that output dir exists (make it if not)
        a. will be /Users/flashton/Dropbox/non-project/test_seqbox_data/Core/[readset_identifier]-filename/
    4. link the fastq to the output_dir
    '''
    if readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'nanopore':
        assert os.path.isfile(readset.readset_nanopore.path_fastq)
    elif readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'illumina':
        assert os.path.isfile(readset.readset_illumina.path_r1)
        assert os.path.isfile(readset.readset_illumina.path_r2)
    # data is going to be stored in a directory with the group name, so need to get the group name of this readset.
    projects = readset.raw_sequencing.extraction.sample.sample_source.projects
    group_names = [x.groups.group_name for x in projects]
    # a sample can only belong to one group, so this assertion should always be true.
    assert len(set(group_names)) == 1
    group_name = group_names[0]
    group_dir = os.path.join(config['seqbox_directory'], group_name)
    if not os.path.isdir(group_dir):
        os.mkdir(group_dir)
    # going to name the linked file with the sample name and readset_identifier
    sample_name = readset.raw_sequencing.extraction.sample.sample_identifier
    readset_dir = os.path.join(group_dir, f"{readset.readset_identifier}-{sample_name}")
    if not os.path.isdir(readset_dir):
        os.mkdir(readset_dir)
    if readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'nanopore':
        output_readset_fastq_path = os.path.join(readset_dir, f"{readset.readset_identifier}-{sample_name}.fastq.gz")
        if os.path.isfile(output_readset_fastq_path):
            print(f"{output_readset_fastq_path} already exists. Exiting.")
            sys.exit()
        else:
            os.symlink(readset.readset_nanopore.path_fastq, output_readset_fastq_path)
    elif readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'illumina':
        output_readset_r1_fastq_path = os.path.join(readset_dir, f"{readset.readset_identifier}-{sample_name}_R1.fastq.gz")
        output_readset_r2_fastq_path = os.path.join(readset_dir, f"{readset.readset_identifier}-{sample_name}_R2.fastq.gz")

        assert os.path.isfile(output_readset_r2_fastq_path) is False
        os.symlink(readset.readset_illumina.path_r1, output_readset_r1_fastq_path)
        os.symlink(readset.readset_illumina.path_r2, output_readset_r2_fastq_path)
    print(f"Added readset to filestructure {readset.readset_identifier}-{sample_name} to {group_dir}")


def run_add_readset_to_filestructure(args):
    config = read_in_config(args.seqbox_config)
    all_readsets_info = read_in_as_dict(args.readsets_inhandle)
    for readset_info in all_readsets_info:
        if basic_check_readset_fields(readset_info) is False:
            continue
        if args.nanopore_default is True:
            readset_nanopre = get_nanopore_readset_from_batch_and_barcode(readset_info)
            if readset_nanopre is False:
                print(f"There is no readset for\n{readset_info}\nExiting.")
                sys.exit()
            else:
                add_readset_to_filestructure(readset_nanopre.readset, config)
        elif args.nanopore_default is False:
            # readset_tech is either readset_illumina or readset_nanopore
            readset_tech = get_readset(readset_info, args.covid)
            if readset_tech is False:
                print(f"There is no readset for\n{readset_info}\nExiting.")
                sys.exit()
            else:
                add_readset_to_filestructure(readset_tech.readset, config)


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
                os.symlink(source_consensus[0], target_consensus)
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
                os.symlink(source_bam[0], target_bam)
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
    parser_add_readset_to_filestructure.add_argument('-s', dest='covid', action='store_true', default=False,
                                     help='Are these readsets SARS-CoV-2?')
    parser_add_readset_to_filestructure.add_argument('-n', dest='nanopore_default', action='store_true', default=False,
                                     help='Are the data for these readsets arranged in nanopore default format? Need to'
                                          ' follow a different template for the inhandle.')

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

    args = parser.parse_args()
    run_command(args)


if __name__ == '__main__':
    main()
