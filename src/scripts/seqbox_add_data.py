import csv
import sys
import pprint
import datetime
from app import db
from app.models import Isolate, ReadSet, IlluminaReadSet, NanoporeReadSet, Project, ReadSetBatch #, Patient


def read_in_as_dict(inhandle):
    # since csv.DictReader returns a generator rather than an iterator, need to do this fancy business to
    # pull in everything from a generator into an honest to goodness iterable.
    info = csv.DictReader(open(inhandle, encoding='utf-8-sig'))
    # info is a list of ordered dicts, so convert each one to
    l = []
    for each_dict in info:
        new_info = {x: each_dict[x] for x in each_dict}
        l.append(new_info)
    return l


def get_projects(isolate_info):
    project_names = [x.strip() for x in isolate_info['projects'].split(';')]
    projects = []
    for project_name in project_names:
        matching_projects = Project.query.filter_by(project_name=project_name, group=isolate_info['group']).all()
        if len(matching_projects) == 0:
            s = Project(project_name=project_name, group=isolate_info['group'])
            projects.append(s)
        elif len(matching_projects) == 1:
            s = matching_projects[0]
            projects.append(s)
        else:
            print(f"There is already more than one project called {project_name} from {isolate_info['group']} in the "
                  f"database, this shouldn't happen.\nExiting.")
            sys.exit()
    return projects


def get_batch(batch_name, group):
    matching_batch = ReadSetBatch.query.filter_by(name=batch_name).all()
    if len(matching_batch) == 0:
        rsb = ReadSetBatch(name=batch_name)
        return rsb
    elif len(matching_batch) == 1:
        return matching_batch[0]
    else:
        print(f"There is already more than one batch called {batch_name} from {group} in the database, "
              "this shouldn't happen.\nExiting.")
        sys.exit()


def return_read_set(rs):
    ## TODO - add nanopore
    ## todo - isn't handling existing readset yet
    batch = get_batch(rs['batch'], rs['group'])
    read_set = ReadSet(type=rs['type'], read_set_filename=rs['read_set_filename'], batch=batch)
    if rs['type'] == 'Illumina':
        irs = IlluminaReadSet(path_r1=rs['path_r1'], path_r2=rs['path_r2'])
        read_set.illumina_read_sets = irs
    return read_set


def add_location(isolate, isolate_info_dict):
    if isolate_info_dict['country'] != '':
        isolate.country = isolate_info_dict['country']
    if isolate_info_dict['city'] != '':
        isolate.location_second_level = isolate_info_dict['city']
    if isolate_info_dict['township'] != '':
        isolate.location_third_level = isolate_info_dict['township']


def get_read_sets(read_set_info, isolate_identifier, group):
    read_sets = []
    # read_set_info is a list of dioctionaries generated from the read set input csv
    # rs is a dictoinary where the keys are the header of the read set input csv, and the values are from one line
    # of the CSV
    for rs in read_set_info:
        if rs['isolate_identifier'] == isolate_identifier:
            if rs['group'] == group:
                read_set = return_read_set(rs)
                read_sets.append(read_set)
    return read_sets


def get_isolate(isolate_identifier):
    matching_isolate = Isolate.query.filter_by(isolate_identifier=isolate_identifier).all()
    if len(matching_isolate) == 0:
        isolate = Isolate(isolate_identifier=isolate_identifier)
        return isolate
    elif len(matching_isolate) == 1:
        return matching_isolate[0]
    else:
        print(f"There is already more than one isolate called {isolate_identifier} in the database, "
              "this shouldn't happen.\nExiting.")
        sys.exit()


def add_isolate(isolate_inhandle):
    all_isolate_info = read_in_as_dict(isolate_inhandle)
    for isolate_info in all_isolate_info:
        isolate = get_isolate(isolate_info['isolate_identifier'])


def add_isolate_and_readset(isolate_inhandle, read_set_inhandle):
    all_isolate_info = read_in_as_dict(isolate_inhandle)
    read_set_info = read_in_as_dict(read_set_inhandle)
    for isolate_info in all_isolate_info:
        projects = get_projects(isolate_info)
        read_sets = get_read_sets(read_set_info, isolate_info['isolate_identifier'], isolate_info['group'])
        # patient = get_patient(isolate_info['patient_identifier'], projects, isolate_info['group'])
        isolate = get_isolate(isolate_info['isolate_identifier'])
        isolate.projects = projects
        isolate.read_sets = read_sets
        add_location(isolate, isolate_info)
        db.session.add(isolate)
    db.session.commit()


def main():
    isolate_inhandle = '/Users/flashton/Dropbox/scripts/seqbox/src/scripts/isolate_example.csv'
    read_set_inhandle = '/Users/flashton/Dropbox/scripts/seqbox/src/scripts/illumina_read_set_example.csv'
    add_isolate_and_readset(isolate_inhandle, read_set_inhandle)
    # add_isolate(isolate_inhandle)
    # todo - need to have a good hard think about how this is going to be used IRL


if __name__ == '__main__':
    main()
