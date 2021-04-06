import csv
import sys
import pprint
from app import db
from app.models import Isolate, ReadSet, IlluminaReadSet, NanoporeReadSet, Study


def get_studies(study_names, group):
    studies = []
    for study_name in study_names:
        matching_studies = Study.query.filter_by(study_name=study_name, group=group).all()
        if len(matching_studies) == 0:
            s = Study(study_name=study_name, group=group)
            studies.append(s)
        elif len(matching_studies) == 1:
            s = matching_studies[0]
            studies.append(s)
        else:
            print(f"There is already more than one study called {study_name} from {group} in the database, "
                  "this shouldn't happen.\nExiting.")
            sys.exit()
    return studies


def return_read_set(rs):
    ## TODO - add nanopore
    read_set = ReadSet(type=rs['type'], read_set_filename=rs['read_set_filename'])
    if rs['type'] == 'Illumina':
        irs = IlluminaReadSet(path_r1=rs['path_r1'], path_r2=rs['path_r2'])
        read_set.illumina_read_sets = irs
    return read_set


def get_read_sets(read_set_info, isolate_identifier, group):
    read_sets = []
    for rs in read_set_info:
        if rs['isolate_identifier'] == isolate_identifier:
            if rs['group'] == group:
                read_set = return_read_set(rs)
                read_sets.append(read_set)
    return read_sets


def get_patient():
    pass


def get_location():
    pass


def add_isolate_and_readset(isolate_inhandle, read_set_inhandle):
    '''
    1. read in 2 files,
        i. isolate file with one line per isolate
        ii. one read set file with one line per read set.
        iii. use csv reader or something, read in as dicts.
    2. take two dicts, one for isolate and one for read set, build:
        i. Isolates with ReadSets
        ii. ReadSets with IlluminaReadSets (linked into readsets above)
        iii. a Study, check if already exists, if not then add it in, if it does exist, add that all the isolates with
            that study to that Study.isolates
    '''
    isolate_info = csv.DictReader(open(isolate_inhandle, encoding='utf-8-sig'))
    read_set_info = csv.DictReader(open(read_set_inhandle, encoding='utf-8-sig'))
    for i in isolate_info:
        study_names = [x.strip() for x in i['studies'].split(';')]
        studies = get_studies(study_names, i['group'])
        read_sets = get_read_sets(read_set_info, i['isolate_identifier'], i['group'])
        # patient = get_patient()
        # location = get_location()
        # isolate = Isolate(isolate_identifier=i['isolate_identifier'], species=i['species'], sample_type=i['sample_type']
        #                   , patient_identifier=patient, date_collected=i['date_collected'],
        #                   location=location, latitude=i['latitude'], longitude=i['longitude'], studies=studies,
        #                   group=i['group'], institution=i['institution'])


def main():
    isolate_inhandle = '/Users/flashton/Dropbox/scripts/seqbox/src/scripts/isolate_example.csv'
    read_set_inhandle = '/Users/flashton/Dropbox/scripts/seqbox/src/scripts/illumina_read_set_example.csv'
    add_isolate_and_readset(isolate_inhandle, read_set_inhandle)


if __name__ == '__main__':
    main()