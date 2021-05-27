import argparse
from seqbox_utils import read_in_as_dict, does_sample_already_exist, add_sample, does_project_already_exist, \
    add_project

# todo - need to handle "what if the isolate source (or isolate) already exists as part of another project",
#  if it is then we don't want to add another isolate, but we want to add another project to that isolate.projects.
#  problem is - how do we know it's the same sample, as opposed to just the same id in two different projects?
#  solution is - isolate and isolate source identifiers have to be unique within a group, AND, isolates and isolate
#  sources cannot be shared between groups.
#  projects belogn to one group

## currently - the test_no_web is not working as expected

def add_samples(args):
    # todo - pull out patient information from input csv, handle adding patients and samples separately
    all_samples_info = read_in_as_dict(args.samples_inhandle)
    for sample_info in all_samples_info:
        if does_sample_already_exist(sample_info) is False:
            add_sample(sample_info)
        # if check_if_sample_exists(sample_info['sample_identifier'], sample_info['group']) is False:


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


def main():
    parser = argparse.ArgumentParser(prog='seqbox_cmd')
    subparsers = parser.add_subparsers(title='[sub-commands]', dest='command')
    parser_add_samples = subparsers.add_parser('add_samples', help='Take a csv file of samples and add to the DB')
    parser_add_samples.add_argument('-i', dest='samples_inhandle', help='A CSV file containing samples'
                                     , required=True)
    parser_add_projects = subparsers.add_parser('add_projects', help='take a csv file of projects and add to the DB')
    parser_add_projects.add_argument('-i', dest='projects_inhandle', help='A CSV file containing projects'
                                     , required=True)
    args = parser.parse_args()
    run_command(args)


if __name__ == '__main__':
    main()
