import sys
import argparse
from seqbox_utils import read_in_as_dict, add_sample, add_project,\
    get_sample_source, add_sample_source, query_projects, \
    get_extraction, add_extraction, add_readset, add_raw_sequencing_batch, get_raw_sequencing_batch, \
    get_tiling_pcr, add_tiling_pcr, get_readset, get_sample, \
    check_sample_source_associated_with_project, get_group, add_group, get_covid_confirmatory_pcr, \
    add_covid_confirmatory_pcr, get_readset_batch, add_readset_batch, get_pcr_result, add_pcr_result, get_pcr_assay, \
    add_pcr_assay, get_artic_covid_result, add_artic_covid_result, get_pangolin_result, add_pangolin_result


allowed_sequencing_types = {'nanopore', 'illumina'}
permitted_artic_workflows = {'medaka'}
permitted_artic_profiles = {'docker'}


def add_groups(args):
    all_groups_info = read_in_as_dict(args.groups_inhandle)
    for group_info in all_groups_info:
        if get_group(group_info) is False:
            add_group(group_info)
        else:
            print(f"Group {group_info['group_name']} already exists for {group_info['institution']}. Not adding this "
                  f"group.")


def add_tiling_pcrs(args):
    all_tiling_pcrs_info = read_in_as_dict(args.tiling_pcrs_inhandle)
    for tiling_pcr_info in all_tiling_pcrs_info:
        if get_tiling_pcr(tiling_pcr_info) is False:
            add_tiling_pcr(tiling_pcr_info)


def add_raw_sequencing_batches(args):
    all_raw_sequencing_batches_info = read_in_as_dict(args.raw_sequencing_batches_inhandle)
    for raw_sequencing_batch_info in all_raw_sequencing_batches_info:
        if raw_sequencing_batch_info['sequencing_type'] not in allowed_sequencing_types:
            print(f"sequencing_type {raw_sequencing_batch_info['sequencing_type']} is not in {allowed_sequencing_types}"
                  f" for this line {raw_sequencing_batch_info}. Exiting.")
            sys.exit()
        if get_raw_sequencing_batch(raw_sequencing_batch_info['batch_name']) is False:
            add_raw_sequencing_batch(raw_sequencing_batch_info)


def add_readset_batches(args):
    all_readset_batches_info = read_in_as_dict(args.readset_batches_inhandle)
    for readset_batch_info in all_readset_batches_info:
        if get_readset_batch(readset_batch_info) is False:
            add_readset_batch(readset_batch_info)
        else:
            print(f"This readset batch {readset_batch_info['readset_batch_name']} is already in the database, "
                  f"not adding it.")


def add_readsets(args):
    all_readsets_info = read_in_as_dict(args.readsets_inhandle)

    for readset_info in all_readsets_info:
        if get_readset(readset_info, args.covid) is False:
            add_readset(readset_info=readset_info, covid=args.covid,
                        nanopore_default=args.nanopore_default)
        else:
            if 'path_fastq' in readset_info:
                print(f"This readset ({readset_info['path_fastq']}) already exists in the database for the group "
                      f"{readset_info['group_name']}. Not adding it to the database.")
            elif 'path_r1' in readset_info:
                print(f"This readset ({readset_info['path_r1']}) already exists in the database for the group "
                      f"{readset_info['group_name']}. Not adding it to the database.")
            elif args.nanopore_default is True:
                print(f"The readset for sample {readset_info['sample_identifier']} for batch {readset_info['readset_batch_name']} "
                      f"is already in the database for group {readset_info['group_name']}. Not adding it to the database.")


def add_extractions(args):
    all_extractions_info = read_in_as_dict(args.extractions_inhandle)
    for extraction_info in all_extractions_info:
        if get_extraction(extraction_info) is False:
            add_extraction(extraction_info)
        else:
            print(f"This extraction ({extraction_info['sample_identifier']}, {extraction_info['extraction_identifier']})"
                  f" on {extraction_info['date_extracted']} already exists in the database for the group "
                  f"{extraction_info['group_name']}")


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
        sample_source = get_sample_source(sample_source_info)
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
            add_project(project_info)
        elif projects_results[0] is True:
            print(f"Project called {project_info['project_name']} from group {project_info['group_name']} already "
                  f"exists, no action will be taken")


def add_covid_confirmatory_pcrs(args):
    all_covid_confirmatory_pcrs_info = read_in_as_dict(args.covid_confirmatory_pcrs_inhandle)
    for covid_confirmatory_pcr_info in all_covid_confirmatory_pcrs_info:
        if get_covid_confirmatory_pcr(covid_confirmatory_pcr_info) is False:
            add_covid_confirmatory_pcr(covid_confirmatory_pcr_info)


def add_pcr_results(args):
    all_pcr_results_info = read_in_as_dict(args.pcr_results_inhandle)
    for pcr_result_info in all_pcr_results_info:
        if get_pcr_result(pcr_result_info) is False:
            add_pcr_result(pcr_result_info)


def add_pcr_assays(args):
    all_pcr_assays_info = read_in_as_dict(args.pcr_assays_inhandle)
    for pcr_assay in all_pcr_assays_info:
        if get_pcr_assay(pcr_assay) is False:
            add_pcr_assay(pcr_assay)


def add_artic_covid_results(args):
    assert args.workflow in permitted_artic_workflows
    assert args.profile in permitted_artic_profiles
    all_artic_covid_results_info = read_in_as_dict(args.artic_covid_results_inhandle)
    for artic_covid_result in all_artic_covid_results_info:
        artic_covid_result['readset_batch_name'] = args.readset_batch_name
        artic_covid_result['barcode'] = artic_covid_result['sample_name'].split('_')[-1]
        artic_covid_result['artic_workflow'] = args.workflow
        artic_covid_result['artic_profile'] = args.profile
        if get_artic_covid_result(artic_covid_result) is False:
            add_artic_covid_result(artic_covid_result)


def add_pangolin_results(args):
    all_pangolin_results_info = read_in_as_dict(args.pangolin_results_inhandle)
    for pangolin_result_info in all_pangolin_results_info:
        pangolin_result_info['readset_batch_name'] = args.readset_batch_name
        pangolin_result_info['barcode'] = pangolin_result_info['taxon'].split('/')[0].split('_')[-1]
        assert pangolin_result_info['barcode'].startswith('barcode')
        assert args.artic_workflow in permitted_artic_workflows
        pangolin_result_info['artic_workflow'] = args.artic_workflow
        assert args.artic_profile in permitted_artic_profiles
        pangolin_result_info['artic_profile'] = args.artic_profile
        if get_pangolin_result(pangolin_result_info) is False:
            add_pangolin_result(pangolin_result_info)


def run_command(args):
    if args.command == 'add_projects':
        add_projects(args=args)
    if args.command == 'add_sample_sources':
        add_sample_sources(args=args)
    if args.command == 'add_samples':
        add_samples(args=args)
    if args.command == 'add_extractions':
        add_extractions(args=args)
    if args.command == 'add_readset_batches':
        add_readset_batches(args=args)
    if args.command == 'add_readsets':
        add_readsets(args=args)
    if args.command == 'add_raw_sequencing_batches':
        add_raw_sequencing_batches(args=args)
    if args.command == 'add_tiling_pcrs':
        add_tiling_pcrs(args=args)
    if args.command == 'add_groups':
        add_groups(args=args)
    if args.command == 'add_covid_confirmatory_pcrs':
        add_covid_confirmatory_pcrs(args=args)
    if args.command == 'get_covid_todo_list':
        print('currently need to get covid todo list through direct sql query. sorry!')
        sys.exit()
    if args.command == 'add_pcr_results':
        add_pcr_results(args=args)
    if args.command == 'add_pcr_assays':
        add_pcr_assays(args=args)
    if args.command == 'add_artic_covid_results':
        add_artic_covid_results(args=args)
    if args.command == 'add_pangolin_results':
        add_pangolin_results(args=args)


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
    parser_add_raw_sequencing_batches = subparsers.add_parser('add_raw_sequencing_batches',
                                                              help='Add information about a raw_sequencing batch')
    parser_add_raw_sequencing_batches.add_argument('-i', dest='raw_sequencing_batches_inhandle')
    parser_add_readsets = subparsers.add_parser('add_readsets',
                                                      help='Take a csv of readsets and add to the DB.')
    parser_add_readsets.add_argument('-i', dest='readsets_inhandle',
                                           help='A CSV file containing readsets info', required=True)
    parser_add_readsets.add_argument('-s', dest='covid', action='store_true', default=False,
                                     help='Are these readsets SARS-CoV-2?')
    parser_add_readsets.add_argument('-n', dest='nanopore_default', action='store_true', default=False,
                                     help='Are the data for these readsets arranged in nanopore default format? Need to'
                                          ' follow a different template for the inhandle.')
    parser_add_extractions = subparsers.add_parser('add_extractions',
                                                help='Take a csv of extractions and add to the DB.')
    parser_add_extractions.add_argument('-i', dest='extractions_inhandle',
                                     help='A CSV file containing extractions info', required=True)
    parser_add_tiling_pcrs = subparsers.add_parser('add_tiling_pcrs',
                                                              help='Add information about a tiling PCR run')
    parser_add_tiling_pcrs.add_argument('-i', dest='tiling_pcrs_inhandle')
    parser_add_groups = subparsers.add_parser('add_groups', help='Add a new group.')
    parser_add_groups.add_argument('-i', dest='groups_inhandle')
    parser_add_covid_confirmatory_pcr = subparsers.add_parser('add_covid_confirmatory_pcrs', help='Add some covid '
                                                                                                  'confirmatory pcrs.')
    parser_add_covid_confirmatory_pcr.add_argument('-i', dest='covid_confirmatory_pcrs_inhandle')
    parser_add_pcr_result = subparsers.add_parser('add_pcr_results', help='Add some PCR results')
    parser_add_pcr_result.add_argument('-i', dest='pcr_results_inhandle')
    parser_add_pcr_assay = subparsers.add_parser('add_pcr_assays', help='Add a PCR assay')
    parser_add_pcr_assay.add_argument('-i', dest='pcr_assays_inhandle')
    parser_get_covid_todo_list = subparsers.add_parser('get_covid_todo_list', help='Get COVID-seq todo list.')
    parser_add_readset_batches = subparsers.add_parser('add_readset_batches', help='Add a readset batch')
    parser_add_readset_batches.add_argument('-i', dest='readset_batches_inhandle')
    parser_add_artic_covid_results = subparsers.add_parser('add_artic_covid_results', help='Add artic nf covid pipeline'
                                                                                           ' results')
    parser_add_artic_covid_results.add_argument('-i', dest='artic_covid_results_inhandle', required=True)
    parser_add_artic_covid_results.add_argument('-b', dest='readset_batch_name', required=True)
    parser_add_artic_covid_results.add_argument('-w', dest='workflow', help='Workflow e.g. illumina, medaka, '
                                                                            'nanopolish', required=True)
    parser_add_artic_covid_results.add_argument('-p', dest='profile', help='Profile e.g. docker, conda, etc',
                                                required=True)
    parser_add_pangolin_results = subparsers.add_parser('add_pangolin_results', help='Pangolin')
    parser_add_pangolin_results.add_argument('-i', dest='pangolin_results_inhandle', required=True)
    parser_add_pangolin_results.add_argument('-b', dest='readset_batch_name', required=True)
    parser_add_pangolin_results.add_argument('-w', dest='artic_workflow',
                                             help='Artic NF Workflow e.g. illumina, medaka, nanopolish used to generate'
                                                  ' the consensus genome', required=True)
    parser_add_pangolin_results.add_argument('-p', dest='artic_profile', help='Artic NF Profile e.g. docker, conda, etc'
                                                                              ' used to generate the consensus genome',
                                             required=True)
    args = parser.parse_args()
    run_command(args)


if __name__ == '__main__':
    main()
