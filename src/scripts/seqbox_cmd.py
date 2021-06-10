import argparse
from seqbox_utils import read_in_as_dict, add_sample, add_project,\
    does_sample_source_already_exist, add_sample_source, query_projects, does_readset_already_exist, \
    get_extraction, add_extraction, add_readset, add_raw_sequencing_batch, get_raw_sequencing_batch, \
    get_tiling_pcr, add_tiling_pcr, get_covid_readset, get_readset, get_sample, check_sample_source_associated_with_project


def add_tiling_pcrs(args):
    all_tiling_pcrs_info = read_in_as_dict(args.tiling_pcrs_inhandle)
    for tiling_pcr_info in all_tiling_pcrs_info:
        if get_tiling_pcr(tiling_pcr_info) is False:
            add_tiling_pcr(tiling_pcr_info)


def add_raw_sequencing_batches(args):
    all_raw_sequencing_batches_info = read_in_as_dict(args.raw_sequencing_batches_inhandle)
    for raw_sequencing_batch_info in all_raw_sequencing_batches_info:
        if get_raw_sequencing_batch(raw_sequencing_batch_info['batch_name']) is False:
            add_raw_sequencing_batch(raw_sequencing_batch_info)


def add_covid_readsets(args):
    all_covid_readsets_info = read_in_as_dict(args.covid_readsets_inhandle)
    for covid_readset_info in all_covid_readsets_info:
        if get_covid_readset(covid_readset_info) is False:
            add_readset(readset_info=covid_readset_info, covid=True)
        else:
            print(f"There is already an extraction for sample {covid_readset_info['sample_identifier']} in the db for "
                  f"{covid_readset_info['date_extracted']} with extraction id "
                  f"{covid_readset_info['extraction_identifier']}. Is this the second extract you did for this sample "
                  f"on this day? If so, increment the extraction id and re-upload.")


def add_readsets(args):
    all_readsets_info = read_in_as_dict(args.readsets_inhandle)
    for readset_info in all_readsets_info:
        if get_readset(readset_info) is False:
            add_readset(readset_info=readset_info, covid=False)


def add_extractions(args):
    all_extractions_info = read_in_as_dict(args.extractions_inhandle)
    for extraction_info in all_extractions_info:
        if get_extraction(extraction_info) is False:
            add_extraction(extraction_info)


def add_samples(args):
    all_samples_info = read_in_as_dict(args.samples_inhandle)
    for sample_info in all_samples_info:
        if get_sample(sample_info) is False:
            add_sample(sample_info)
        else:
            print(f"This sample ({sample_info['sample_identifier']}) already exists in the database for the group "
                  f"{sample_info['group_name']}")
        # if check_if_sample_exists(sample_info['sample_identifier'], sample_info['group']) is False:


def add_sample_sources(args):
    all_sample_source_info = read_in_as_dict(args.sample_sources_inhandle)
    for sample_source_info in all_sample_source_info:
        sample_source = does_sample_source_already_exist(sample_source_info)
        if sample_source is False:
            add_sample_source(sample_source_info)
        else:
            print(
                f"This sample source ({sample_source_info['sample_source_identifier']}) already exists in the database "
                f"for the group {sample_source_info['group_name']}")

            check_sample_source_associated_with_project(sample_source, sample_source_info)


def add_projects(args):
    all_projects_info = read_in_as_dict(args.projects_inhandle)
    for project_info in all_projects_info:
        # query_projects takes project_info['project_name'] as well as project_info because 'project_name' isn't
        # always in the dictionary which this function takes
        projects_results = query_projects(project_info, project_info['project_name'])
        if projects_results[0] is False:
            print(f"Project called {project_info['project_name']} from group "
                  f"{project_info['group_name']} doesn't exist, creating project in DB")
            add_project(project_info)
        elif projects_results[0] is True:
            print(f"Project called {project_info['project_name']} from group {project_info['group_name']} already "
                  f"exists, no action will be taken")


def run_command(args):
    if args.command == 'add_projects':
        add_projects(args=args)
    if args.command == 'add_sample_sources':
        add_sample_sources(args=args)
    if args.command == 'add_samples':
        add_samples(args=args)
    if args.command == 'add_extractions':
        add_extractions(args=args)
    if args.command == 'add_readsets':
        add_readsets(args=args)
    if args.command == 'add_raw_sequencing_batches':
        add_raw_sequencing_batches(args=args)
    if args.command == 'add_tiling_pcrs':
        add_tiling_pcrs(args=args)
    if args.command == 'add_covid_readsets':
        add_covid_readsets(args=args)


def main():
    parser = argparse.ArgumentParser(prog='seqbox_cmd')
    subparsers = parser.add_subparsers(title='[sub-commands]', dest='command')
    parser_add_samples = subparsers.add_parser('add_samples', help='Take a csv file of samples and add to the DB')
    parser_add_samples.add_argument('-i', dest='samples_inhandle', help='A CSV file containing samples'
                                     , required=True)
    parser_add_projects = subparsers.add_parser('add_projects', help='take a csv file of projects and add to the DB')
    parser_add_projects.add_argument('-i', dest='projects_inhandle', help='A CSV file containing projects'
                                     , required=True)
    parser_add_sample_sources = subparsers.add_parser('add_sample_sources',
                                                      help='Take a csv of sample sources and add to the DB.')
    parser_add_sample_sources.add_argument('-i', dest='sample_sources_inhandle',
                                           help='A CSV file containing sample_source info', required=True)
    parser_add_readsets = subparsers.add_parser('add_readsets',
                                                      help='Take a csv of readsets and add to the DB.')
    parser_add_readsets.add_argument('-i', dest='readsets_inhandle',
                                           help='A CSV file containing read_sets info', required=True)
    parser_add_extractions = subparsers.add_parser('add_extractions',
                                                help='Take a csv of extractions and add to the DB.')
    parser_add_extractions.add_argument('-i', dest='extractions_inhandle',
                                     help='A CSV file containing extractions info', required=True)
    parser_add_raw_sequencing_batches = subparsers.add_parser('add_raw_sequencing_batches',
                                                              help='Add information about a raw_sequencing batch')
    parser_add_raw_sequencing_batches.add_argument('-i', dest='raw_sequencing_batches_inhandle')
    parser_add_tiling_pcrs = subparsers.add_parser('add_tiling_pcrs',
                                                              help='Add information about a tiling PCR run')
    parser_add_tiling_pcrs.add_argument('-i', dest='tiling_pcrs_inhandle')
    parser_add_covid_readsets = subparsers.add_parser('add_covid_readsets',
                                                   help='Add information about a tiling PCR run')
    parser_add_covid_readsets.add_argument('-i', dest='covid_readsets_inhandle')
    args = parser.parse_args()
    run_command(args)


if __name__ == '__main__':
    main()
