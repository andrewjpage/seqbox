import argparse
from seqbox_utils import read_in_as_dict, does_isolate_already_exist, add_isolate, does_project_already_exist, \
    add_project


def add_isolates(args):
    # todo - pull out patient information from input csv, handle adding patients and isolates separately
    all_isolate_info = read_in_as_dict(args.isolates_inhandle)
    for isolate_info in all_isolate_info:
        if does_isolate_already_exist(isolate_info['isolate_identifier'], isolate_info['group_name']) is False:
            add_isolate(isolate_info)
        # if check_if_isolate_exists(isolate_info['isolate_identifier'], isolate_info['group']) is False:


def add_projects(args):
    all_projects_info = read_in_as_dict(args.projects_inhandle)
    for project_info in all_projects_info:
        if does_project_already_exist(project_info) is False:
            add_project(project_info)


def run_command(args):
    if args.command == 'add_isolates':
        add_isolates(args=args)
    if args.command == 'add_projects':
        add_projects(args=args)


def main():
    parser = argparse.ArgumentParser(prog='seqbox_cmd')
    subparsers = parser.add_subparsers(title='[sub-commands]', dest='command')
    parser_add_isolates = subparsers.add_parser('add_isolates', help='Take a csv file of isolates and add to the DB')
    parser_add_isolates.add_argument('-i', dest='isolates_inhandle', help='A CSV file containing isolates'
                                     , required=True)
    parser_add_projects = subparsers.add_parser('add_projects', help='take a csv file of projects and add to the DB')
    parser_add_projects.add_argument('-i', dest='projects_inhandle', help='A CSV file containing projects'
                                     , required=True)
    args = parser.parse_args()
    run_command(args)


if __name__ == '__main__':
    main()
