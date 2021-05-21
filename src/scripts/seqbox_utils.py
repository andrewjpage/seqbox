import csv
import sys
from app import db
from app.models import Isolate, Project, Patient, ReadSet, IlluminaReadSet, ReadSetBatch


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


def does_isolate_already_exist(isolate_identifier, group):
    # this function checks if this isolate identifier has already been used by this group, and if so,
    # returns True, if not it returns false
    # the aim of this query is to get a list of all the isolate identifiers belonging to a specific group
    # this does a join of isolate and projects (via magic), and the filters by the group_name
    # https://stackoverflow.com/questions/40699642/how-to-query-many-to-many-sqlalchemy
    all = Isolate.query.with_entities(Isolate.isolate_identifier).join(Isolate.projects)\
        .filter_by(group_name=group)\
        .distinct()
    # have to do this extra bit in python becayse couldn't figure out how to do another "where" in the above query
    # would just have to do `where Isolate.isolate_identifier == isolate_identifier`
    isolates_from_this_group = set([i[0] for i in all])
    if isolate_identifier in isolates_from_this_group:
        print(f"This isolate ({isolate_identifier}) already exists in the database for the group {group}")
        return True
    else:
        return False


def does_project_already_exist(project_info):
    matching_projects = Project.query.filter_by(project_name=project_info['project_name'],
                                                group_name=project_info['group_name']).all()
    if len(matching_projects) == 0:
        print(f"Project called {project_info['project_name']} from group "
              f"{project_info['group_name']} doesn't exist, creating project in DB")
        return False
    elif len(matching_projects) == 1:
        print(f"Project called {project_info['project_name']} from group "
              f"{project_info['group_name']} already exists, no action will be taken")
        return True
    else:
        print(f"there is more than one project called {project_info['project_name']} from group "
              f"{project_info['group_name']} - this shouldn't happen, exiting")
        sys.exit()


def add_project(project_info):
    project = Project(project_name=project_info['project_name'], group_name=project_info['group_name'],
                      institution=project_info['institution'], project_details=project_info['project_details'])
    db.session.add(project)
    db.session.commit()


def get_projects(isolate_info):
    project_names = [x.strip() for x in isolate_info['projects'].split(';')]
    projects = []
    for project_name in project_names:
        matching_projects = Project.query.filter_by(project_name=project_name,
                                                    group_name=isolate_info['group_name'],
                                                    instituion=isolate_info['institution']).all()
        if len(matching_projects) == 0:
            print(f"Project {project_name} from group {isolate_info['group_name']} from institution "
                  f"{isolate_info['institution']} doesnt exist in the db, you need to add it using the seqbox_cmd.py "
                  f"add_projects function.\nExiting now.")
            # todo - print a list of all the project names in case of typo
            sys.exit()
        elif len(matching_projects) == 1:
            s = matching_projects[0]
            projects.append(s)
        else:
            print(f"There is already more than one project called {project_name} from {isolate_info['group_name']} at "
                  f"{isolate_info['institution']} in the database, this shouldn't happen.\nExiting.")
            sys.exit()
    return projects


def get_patient(isolate_info):
    matching_patient = Patient.query.join(Patient.projects).\
        filter_by(patient_identifier=isolate_info['patient_identifier'])


def read_in_isolate_info(isolate_info):
    isolate = Isolate(isolate_identifier=isolate_info['isolate_identifier'])
    if isolate_info['species'] != '':
        isolate.species = isolate_info['species']
    if isolate_info['sample_type'] != '':
        isolate.sample_type = isolate_info['sample_type']
    if isolate_info['patient_identifier'] != '':
        isolate.patient_identifier = isolate_info['patient_identifier']
    if isolate_info['day_collected'] != '':
        isolate.day_collected = isolate_info['day_collected']
    if isolate_info['month_collected'] != '':
        isolate.month_collected = isolate_info['month_collected']
    if isolate_info['year_collected'] != '':
        isolate.year_collected = isolate_info['year_collected']
    if isolate_info['township'] != '':
        isolate.location_third_level = isolate_info['township']
    if isolate_info['city'] != '':
        isolate.location_second_level = isolate_info['city']
    if isolate_info['country'] != '':
        isolate.country = isolate_info['country']
    if isolate_info['latitude'] != '':
        isolate.latitude = isolate_info['latitude']
    if isolate_info['longitude'] != '':
        isolate.longitude = isolate_info['longitude']
    return isolate

def add_isolate(isolate_info):
    # isolate_info is a dict of one line of the input csv (keys from col header)
    # for the projects listed in the csv, check if they already exist for that group
    # if it does, return it, if it doesnt, instantiate a new Project and return it
    projects = get_projects(isolate_info)
    # todo - shift add_patients to a seqbox_cmd thing,
    # todo -
    patient = get_patient(isolate_info)
    # instantiate a new Isolate
    isolate = read_in_isolate_info(isolate_info)

    isolate.projects = projects
    db.session.add(isolate)
    db.session.commit()


# def get_read_sets(read_set_info, isolate_identifier, group):
#     read_sets = []
#     # read_set_info is a list of dioctionaries generated from the read set input csv
#     # rs is a dictoinary where the keys are the header of the read set input csv, and the values are from one line
#     # of the CSV
#     for rs in read_set_info:
#         if rs['isolate_identifier'] == isolate_identifier:
#             if rs['group'] == group:
#                 read_set = return_read_set(rs)
#                 read_sets.append(read_set)
#     return read_sets


# def return_read_set(rs):
#     ## TODO - add nanopore
#     ## todo - isn't handling existing readset yet
#     batch = get_batch(rs['batch'], rs['group'])
#     read_set = ReadSet(type=rs['type'], read_set_filename=rs['read_set_filename'], batch=batch)
#     if rs['type'] == 'Illumina':
#         irs = IlluminaReadSet(path_r1=rs['path_r1'], path_r2=rs['path_r2'])
#         read_set.illumina_read_sets = irs
#     return read_set


# def get_batch(batch_name, group):
#     matching_batch = ReadSetBatch.query.filter_by(name=batch_name).all()
#     if len(matching_batch) == 0:
#         rsb = ReadSetBatch(name=batch_name)
#         return rsb
#     elif len(matching_batch) == 1:
#         return matching_batch[0]
#     else:
#         print(f"There is already more than one batch called {batch_name} from {group} in the database, "
#               "this shouldn't happen.\nExiting.")
#         sys.exit()