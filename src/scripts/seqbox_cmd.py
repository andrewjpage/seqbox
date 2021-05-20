import argparse
from seqbox_utils import read_in_as_dict, check_if_isolate_exists, add_isolate


def add_isolates(args):
    all_isolate_info = read_in_as_dict(args.isolates_inhandle)
    for isolate_info in all_isolate_info:
        if check_if_isolate_exists(isolate_info['isolate_identifier'], isolate_info['group']) is False:
            add_isolate(isolate_info)


def run_command(args):
    if args.command == 'add_isolates':
        add_isolates(args=args)


def main():
    parser = argparse.ArgumentParser(prog='seqbox_cmd')
    subparsers = parser.add_subparsers(title='[sub-commands]', dest='command')
    parser_add_isolates = subparsers.add_parser('add_isolates', help='Takes a list of fastqs and puts them in the '
                                                                     'oucru_robot directory structure')
    parser_add_isolates.add_argument('-i', dest='isolates_inhandle', help='A CSV file containing '
                                     , required=True)

    args = parser.parse_args()
    run_command(args)


if __name__ == '__main__':
    main()
