import argparse
from seqbox_utils import read_in_as_dict, does_sample_already_exist, add_sample, does_project_already_exist, \
    add_project, does_sample_source_already_exist, add_sample_source


def add_samples(args):
    all_samples_info = read_in_as_dict(args.samples_inhandle)
    for sample_info in all_samples_info:
        if does_sample_already_exist(sample_info) is False:
            add_sample(sample_info)
        # if check_if_sample_exists(sample_info['sample_identifier'], sample_info['group']) is False:


def add_sample_sources(args):
    all_sample_source_info = read_in_as_dict(args.sample_sources_inhandle)
    for sample_source_info in all_sample_source_info:
        if does_sample_source_already_exist(sample_source_info) is False:
            add_sample_source(sample_source_info)


def add_projects(args):
    all_projects_info = read_in_as_dict(args.projects_inhandle)
    for project_info in all_projects_info:
        if does_project_already_exist(project_info) is False:
            add_project(project_info)


def run_command(args):
    if args.command == 'add_samples':
        add_samples(args=args)
    if args.command == 'add_projects':
        add_projects(args=args)
    if args.command == 'add_sample_sources':
        add_sample_sources(args=args)


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
    args = parser.parse_args()
    run_command(args)


if __name__ == '__main__':
    main()
