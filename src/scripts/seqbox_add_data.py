import csv
import sys
import pprint
import datetime
from app import db
from app.models import Isolate, ReadSet, IlluminaReadSet, NanoporeReadSet, Project, ReadSetBatch #, Patient


def get_projects(project_names, group):
    projects = []
    for project_name in project_names:
        matching_projects = Project.query.filter_by(project_name=project_name, group=group).all()
        if len(matching_projects) == 0:
            s = Project(project_name=project_name, group=group)
            projects.append(s)
        elif len(matching_projects) == 1:
            s = matching_projects[0]
            projects.append(s)
        else:
            print(f"There is already more than one project called {project_name} from {group} in the database, "
                  "this shouldn't happen.\nExiting.")
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
    for rs in read_set_info:
        if rs['isolate_identifier'] == isolate_identifier:
            if rs['group'] == group:
                read_set = return_read_set(rs)
                read_sets.append(read_set)
    return read_sets


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


def add_isolate_and_readset(isolate_inhandle, read_set_inhandle):
    isolate_info = read_in_as_dict(isolate_inhandle)
    read_set_info = read_in_as_dict(read_set_inhandle)
    for i in isolate_info:
        # print(i)
        # print(i['isolate_identifier'])
        project_names = [x.strip() for x in i['projects'].split(';')]
        projects = get_projects(project_names, i['group'])
        read_sets = get_read_sets(read_set_info, i['isolate_identifier'], i['group'])
        # patient = get_patient(i['patient_identifier'], projects, i['group'])
        # date_collected = datetime.datetime.strptime(i['date_collected'], '%d/%m/%Y')
        isolate = Isolate(isolate_identifier=i['isolate_identifier'], species=i['species'], sample_type=i['sample_type']
                          , read_sets=read_sets, day_collected=i['day_collected'], month_collected=i['month_collected'],
                          year_collected=i['year_collected'], latitude=float(i['latitude']),
                          longitude=float(i['longitude']), projects=projects, institution=i['institution'],
                          patient_identifier=i['patient_identifier'],)
        add_location(isolate, i)
        db.session.add(isolate)
    db.session.commit()


def main():
    isolate_inhandle = '/Users/flashton/Dropbox/scripts/seqbox/src/scripts/isolate_example.csv'
    read_set_inhandle = '/Users/flashton/Dropbox/scripts/seqbox/src/scripts/illumina_read_set_example.csv'
    add_isolate_and_readset(isolate_inhandle, read_set_inhandle)


if __name__ == '__main__':
    main()
