import os
import csv
import sys
import glob
import datetime
import pandas as pd
import numpy as np
from app import db#, engine, conn
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from app.models import Sample, Project, SampleSource, ReadSet, ReadSetIllumina, ReadSetNanopore, RawSequencingBatch,\
    Extraction, RawSequencing, RawSequencingNanopore, RawSequencingIllumina, TilingPcr, Groups, CovidConfirmatoryPcr, \
    ReadSetBatch, PcrResult, PcrAssay, ArticCovidResult, PangolinResult, Culture, Mykrobe


def replace_with_none(each_dict):
    """
    This func takes in a dict object & replaces the empty string values with None
    """
    return {k:None if not v else v for k,v in each_dict.items()}


def convert_to_datetime_dict(each_dict):
    """
    This func takes in a dict & takes out keys containing 'date' &
    convert their values to a datetime object
    """
    dated_entry = [ key for key in each_dict.keys() if 'date' in key]
    for entry in dated_entry:
        if each_dict[entry]:
            each_dict[entry] = datetime.datetime.strptime(each_dict[entry],'%d/%m/%Y')
    return each_dict


def read_in_csv(inhandle):
    # since csv.DictReader returns a generator rather than an iterator, need to do this fancy business to
    # pull in everything from a generator into an honest to goodness iterable.
    info = csv.DictReader(open(inhandle, encoding='utf-8-sig'))
    # info is a list of ordered dicts, so convert each one to
    list_of_lines = []
    for each_dict in info:
        # print(each_dict)
        # delete data from columns with no header, usually just empty fields
        if None in each_dict:
            del each_dict[None]
        new_info = {x: each_dict[x] for x in each_dict}
        # print(new_info)
        # sometimes excel saves blank lines, so only take lines where the lenght of the set of teh values is > 1
        # it will be 1 where they are all blank i.e. ''
        if len(set(new_info.values())) > 1:
            list_of_lines.append(new_info)
        # because pcr assay only has one value, need to add this check
        elif len(set(new_info.values())) == 1:
            if list(set(new_info.values()))[0] == '':
                pass
            else:
                list_of_lines.append(new_info)
        else:
            pass
            # print(f'This line not being processed - {new_info}')
    return list_of_lines


def convert_to_datetime_df(df):
    """
    This func takes in a dataframe & returns a dataframe with cols containing 'date'
    in them properly converted to a datetime obj
    """
    # Get columns with date in them & convert them to datetime
    dated_cols = df.filter(like='date').columns
    convert_dict = {dated_col: 'datetime64[ns]' for dated_col in dated_cols}
    return df.astype(convert_dict)


def read_in_excel(file):
    df = pd.read_excel(file)
    df_len = len(df)

    df = convert_to_datetime_df(df)
    # convert both nans & NaT to None
    df.replace({pd.NaT:None,np.nan:None},inplace=True)

    list_of_lines = [df.iloc[i].to_dict() for i in range(df_len)]
    return list_of_lines


def read_in_as_dict(inhandle):
    # Check file type i.e is it a csv or xls(x)? then proceed to read accordingly
    if inhandle.endswith('.csv'):
        data = read_in_csv(inhandle)
    elif inhandle.endswith('.xlsx') or inhandle.endswith('.xlx'):
        data = read_in_excel(inhandle)
    else:
        print("Invalid file format")
        sys.exit(1)
    return data


def check_sample_source_associated_with_project(sample_source, sample_source_info):
    # todo - maybe just get rid of this pathway, and have a different seqbox_cmd function for if you want to add a new
    #  relationship between an existing sample source and project
    # sample_source_info is a line from the input csv
    # sample_source is the corresponding entry from the DB
    # get the projects from the input file as set
    projects_from_input_file = sample_source_info['projects'].split(';')
    projects_from_input_file = set([x.strip() for x in projects_from_input_file])
    # get the projects from the db for this sample_source
    projects_from_db = set([x.project_name for x in sample_source.projects])
    # are there any sample_source to project relationships in the file which aren't represented in the db?
    new_projects_from_file = projects_from_input_file - projects_from_db
    # if there are any
    if len(new_projects_from_file) > 0:
        # then, for each one
        for project_name in new_projects_from_file:
            print(f"Adding existing sample_source {sample_source_info['sample_source_identifier']} to project "
                  f"{project_name}")
            # query projects, this will only return p[0] is True if the project name already exists for this group
            # otherwise, they need to add the project and re-run.
            p = query_projects(sample_source_info, project_name)
            if p[0] is True:
                # add it to the projects assocaited with this sample source
                sample_source.projects.append(p[1])
            else:
                print(f"Checking that sample source is associated with project. "
                      f"Project {project_name} from group {sample_source_info['group_name']} "
                      f" doesnt exist in the db, you need to add it using the seqbox_cmd.py "
                      f"add_projects function.\nExiting now.")
                sys.exit(1)
    # and update the database.
    db.session.commit()


def get_sample_source(sample_info):
    # want to find whether this sample_source is already part of this project
    matching_sample_source = SampleSource.query.\
        filter_by(sample_source_identifier=sample_info['sample_source_identifier'])\
        .join(SampleSource.projects) \
        .join(Groups)\
        .filter_by(group_name=sample_info['group_name']).all()
    if len(matching_sample_source) == 0:
        return False
    elif len(matching_sample_source) == 1:
        return matching_sample_source[0]
    else:
        print(f"Trying to get sample_source. "
              f"There is more than one matching sample_source with the sample_source_identifier "
              f"{sample_info['sample_source_identifier']} for group {sample_info['group_name']}, This shouldn't happen."
              f" Exiting.")


def get_sample(readset_info):
    matching_sample = Sample.query \
        .filter_by(sample_identifier=readset_info['sample_identifier']) \
        .join(SampleSource) \
        .join(SampleSource.projects) \
        .join(Groups) \
        .filter_by(group_name=readset_info['group_name']).distinct().all()

    if len(matching_sample) == 0:
        return False
    elif len(matching_sample) == 1:
        return matching_sample[0]
    else:
        print(f"Trying to get sample. There is more than one matching sample with the sample_identifier "
              f"{readset_info['sample_identifier']} for group {readset_info['group_name']}, This shouldn't happen. "
              f"Exiting.")
        sys.exit(1)


def update_sample(sample):
    sample.submitted_for_sequencing = True
    db.session.commit()


def get_mykrobe_result(mykrobe_result_info):
    matching_mykrobe_result = Mykrobe.query. \
        filter_by(mykrobe_version=mykrobe_result_info['mykrobe_version'], drug=mykrobe_result_info['drug']) \
        .join(ReadSet).filter_by(readset_identifier=mykrobe_result_info['readset_identifier']).distinct().all()
    if len(matching_mykrobe_result) == 0:
        return False
    elif len(matching_mykrobe_result) == 1:
        return matching_mykrobe_result[0]
    else:
        print(f"Trying to get mykrobe_result. There is more than one matching mykrobe_result with the sample_identifier "
              f"{mykrobe_result_info['sample_identifier']} for group {mykrobe_result_info['group_name']}, "
              f"This shouldn't happen. Exiting.")
        sys.exit(1)

def get_extraction(readset_info):
    matching_extraction = None
    # todo - could replace this with a union query
    if readset_info['extraction_from'] == 'whole_sample':
        matching_extraction = Extraction.query.filter_by(extraction_identifier=readset_info['extraction_identifier'],
                                                         date_extracted=readset_info['date_extracted']) \

            .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier'])\
            .join(SampleSource)\
            .join(SampleSource.projects) \
            .join(Groups) \
            .filter_by(group_name=readset_info['group_name'])\
            .all()
    elif readset_info['extraction_from'] == 'cultured_isolate':
        matching_extraction = Extraction.query.filter_by(extraction_identifier=readset_info['extraction_identifier'],
                                                         date_extracted=readset_info['date_extracted']) \

            .join(Culture) \
            .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier']) \
            .join(SampleSource) \
            .join(SampleSource.projects) \
            .join(Groups) \
            .filter_by(group_name=readset_info['group_name']) \
            .all()
    if len(matching_extraction) == 1:
        return matching_extraction[0]
    elif len(matching_extraction) == 0:
        return False
    else:
        print(f"Trying to get extraction. "
              f"More than one Extraction match for {readset_info['sample_identifier']}. Shouldn't happen, exiting.")
        sys.exit(1)


def get_culture(culture_info):

    matching_culture = Culture.query.filter_by(
            culture_identifier=culture_info['culture_identifier'],
                                               date_cultured=culture_info['date_cultured']) \
        .join(Sample).filter_by(sample_identifier=culture_info['sample_identifier']) \
        .join(SampleSource) \
        .join(SampleSource.projects) \
        .join(Groups) \
        .filter_by(group_name=culture_info['group_name']) \
        .all()
    if len(matching_culture) == 1:
        return matching_culture[0]
    elif len(matching_culture) == 0:
        return False
    else:
        print(f"Trying to get culture. "
              f"More than one Culture match for {culture_info['sample_identifier']}. Shouldn't happen, exiting.")
        sys.exit(1)


def add_project(project_info):
    group = get_group(project_info)
    if group is False:
        print(f"Trying to get group to add project. "
              f"No group {project_info['group_name']} from institution {project_info['institution']}. You need to add "
              f"this group. Exiting.")
        sys.exit(1)
    project = Project(project_name=project_info['project_name'], project_details=project_info['project_details'])
    group.projects.append(project)
    db.session.add(project)
    db.session.commit()
    print(f"Added project {project_info['project_name']} to group {project_info['group_name']} at "
          f"{project_info['institution']}.")


def add_readset_batch(readset_batch_info):
    raw_sequencing_batch = get_raw_sequencing_batch(readset_batch_info['raw_sequencing_batch_name'])
    if raw_sequencing_batch is False:
        print(f"Trying to get raw sequencing batch to add read set batch. "
              f"No raw sequencing batch {readset_batch_info['raw_sequencing_batch_name']}. You need to add "
              f"this raw sequencing batch. Exiting.")
        sys.exit(1)
    readset_batch = read_in_readset_batch(readset_batch_info)
    raw_sequencing_batch.readset_batches.append(readset_batch)
    db.session.commit()
    print(f"Added readset batch {readset_batch_info['raw_sequencing_batch_name']}.")


def query_projects(info, project_name):
    matching_projects = Project.query.filter_by(project_name=project_name).join(Groups)\
        .filter_by(group_name=info['group_name'], institution=info['institution']).all()
    if len(matching_projects) == 0:
        # need this to have the `,` so that can evaluate the return correctly for the elif section
        return False,
    elif len(matching_projects) == 1:
        s = matching_projects[0]
        return True, s
    else:
        print(f"Querying projects. "
              f"There is already more than one project called {project_name} from {info['group_name']} at "
              f"{info['institution']} in the database, this shouldn't happen.\nExiting.")
        sys.exit(1)


def get_projects(info):
    assert 'projects' in info
    assert 'group_name' in info
    project_names = [x.strip() for x in info['projects'].split(';')]
    projects = []
    for project_name in project_names:
        p = query_projects(info, project_name)
        if p[0] is True:
            projects.append(p[1])
        elif p[0] is False:
            print(f"Getting projects. Project {project_name} from group {info['group_name']} "
                  f" doesnt exist in the db, you need to add it using the seqbox_cmd.py "
                  f"add_projects function.\nExiting now.")
            sys.exit(1)
    return projects


def get_artic_covid_result(artic_covid_result_info):
    # check_artic_covid_result(artic_covid_result) - check that profile and workflow are in allowed lists.
    matching_artic_covid_result = ArticCovidResult.query.filter_by(profile=artic_covid_result_info['artic_profile'],
                                                                workflow=artic_covid_result_info['artic_workflow'])\
        .join(ReadSet)\
        .join(ReadSetBatch).filter_by(name=artic_covid_result_info['readset_batch_name'])\
        .join(ReadSetNanopore).filter_by(barcode=artic_covid_result_info['barcode']).all()
    if len(matching_artic_covid_result) == 1:
        return matching_artic_covid_result[0]
    elif len(matching_artic_covid_result) == 0:
        return False
    else:
        print(f"Trying to get artic_covid_result. "
              f"More than one ArticCovidResult for barcode {artic_covid_result_info['barcode']} for "
              f"readset batch {artic_covid_result_info['readset_batch_name']}, run with profile {artic_covid_result_info['profile']} "
              f"and workflow {artic_covid_result_info['artic_workflow']}. Shouldn't happen, exiting.")
        sys.exit(1)


def get_pangolin_result(pangolin_result_info):
    matching_pangolin_result = PangolinResult.query.filter_by(version=pangolin_result_info['version']) \
        .join(ArticCovidResult)\
        .filter_by(profile=pangolin_result_info['artic_profile'], workflow=pangolin_result_info['artic_workflow'])\
        .join(ReadSet)\
        .join(ReadSetBatch).filter_by(name=pangolin_result_info['readset_batch_name'])\
        .join(ReadSetNanopore).filter_by(barcode=pangolin_result_info['barcode']).all()
    if len(matching_pangolin_result) == 1:
        return matching_pangolin_result[0]
    elif len(matching_pangolin_result) == 0:
        return False
    else:
        print(f"Trying to get pangolin_result. "
              f"More than one PangolinResult for version {pangolin_result_info['version']} "
              f"barcode {pangolin_result_info['barcode']} for readset batch"
              f"{pangolin_result_info['readset_batch_name']}, run with profile {pangolin_result_info['artic_profile']} "
              f"and workflow {pangolin_result_info['artic_workflow']}. Shouldn't happen, exiting.")
        sys.exit(1)


def read_in_sample_info(sample_info):
    check_samples(sample_info)
    sample = Sample(sample_identifier=sample_info['sample_identifier'])
    if sample_info['species'] != '':
        sample.species = sample_info['species']
    if sample_info['sample_type'] != '':
        sample.sample_type = sample_info['sample_type']
    if sample_info['sample_source_identifier'] != '':
        sample.sample_source_id = sample_info['sample_source_identifier']
    if sample_info['day_collected'] != '':
        sample.day_collected = sample_info['day_collected']
    if sample_info['month_collected'] != '':
        sample.month_collected = sample_info['month_collected']
    if sample_info['year_collected'] != '':
        sample.year_collected = sample_info['year_collected']
    if sample_info['day_received'] != '':
        sample.day_received = sample_info['day_received']
    if sample_info['month_received'] != '':
        sample.month_received = sample_info['month_received']
    if sample_info['year_received'] != '':
        sample.year_received = sample_info['year_received']
    if sample_info['sequencing_type_requested'] != '':
        sample.sequencing_type_requested = sample_info['sequencing_type_requested'].split(';')
    if sample_info['submitter_plate_id'].startswith('SAM'):
        sample.submitter_plate_id = sample_info['submitter_plate_id']
        sample.submitter_plate_well = sample_info['submitter_plate_well']
    # if the submitter_plate_id starts with OUT, then the sample is an externally sequenced sample and has no plate info
    elif sample_info['submitter_plate_id'].startswith('OUT'):
        sample.submitter_library_plate_id = sample_info['submitter_plate_id']
        sample.submitter_library_plate_well = None
    return sample


def read_in_sample_source_info(sample_source_info):
    check_sample_sources(sample_source_info)
    sample_source = SampleSource(sample_source_identifier=sample_source_info['sample_source_identifier'])
    
    if sample_source_info['sample_source_type'] != '':
        sample_source.sample_source_type = sample_source_info['sample_source_type']
    if sample_source_info['township'] != '':
        sample_source.location_third_level = sample_source_info['township']
    if sample_source_info['city'] != '':
        sample_source.location_second_level = sample_source_info['city']
    if sample_source_info['country'] != '':
        sample_source.country = sample_source_info['country']
    if sample_source_info['latitude'] != '':
        sample_source.latitude = sample_source_info['latitude']
    if sample_source_info['longitude'] != '':
        sample_source.longitude = sample_source_info['longitude']
    
    return sample_source


def read_in_culture(culture_info):
    if check_cultures(culture_info) is False:
        sys.exit(1)
    culture = Culture()

    culture.date_cultured = culture_info['date_cultured']
    culture.culture_identifier = culture_info['culture_identifier']
    # if the submitter_plate_id starts with SAM, then the culture is a culture that was created in the lab
    # if the submitter_plate_id starts with OUT, then the culture is an externally sequenced culture and has no
    # submitter plate info
    if culture_info['submitter_plate_id'].startswith('SAM'):
        culture.submitter_plate_id = culture_info['submitter_plate_id']
        culture.submitter_plate_well = culture_info['submitter_plate_well']
    elif culture_info['submitter_plate_id'].startswith('OUT'):
        culture.submitter_plate_id = culture_info['submitter_plate_id']
        culture.submitter_plate_well = None
    return culture


def read_in_extraction(extraction_info):
    extraction = Extraction()
    # Proposal: Get rid of the 'if checks' because by this time we have already checked the validity extraction_info fields

    if extraction_info['extraction_identifier']:
        extraction.extraction_identifier = extraction_info['extraction_identifier']

    if extraction_info['extraction_machine']:
        extraction.extraction_machine = extraction_info['extraction_machine']

    if extraction_info['extraction_kit']:
        extraction.extraction_kit = extraction_info['extraction_kit']

    if extraction_info['what_was_extracted']:
        extraction.what_was_extracted = extraction_info['what_was_extracted']

    if extraction_info['date_extracted']:
        extraction.date_extracted = extraction_info['date_extracted']

    if extraction_info['extraction_processing_institution']:
        extraction.processing_institution = extraction_info['extraction_processing_institution']

    if extraction_info['extraction_from']:
        extraction.extraction_from = extraction_info['extraction_from']

    if extraction_info['nucleic_acid_concentration']:
        extraction.nucleic_acid_concentration = extraction_info['nucleic_acid_concentration']

    if extraction_info['submitter_plate_id'].startswith('EXT'):
        extraction.submitter_plate_id = extraction_info['submitter_plate_id']
        extraction.submitter_plate_well = extraction_info['submitter_plate_well']
    elif extraction_info['submitter_plate_id'].startswith('OUT'):
        extraction.submitter_plate_id = extraction_info['submitter_plate_id']
        extraction.submitter_plate_well = None
    return extraction


def read_in_group(group_info):
    check_group(group_info)
    group = Groups()
    group.group_name = group_info['group_name']
    group.institution = group_info['institution']
    group.pi = group_info['pi']
    return group


def check_mykrobe_res(mykrobe_res_info):
    for field in ['sample', 'drug', 'susceptibility', 'mykrobe_version']:
        if mykrobe_res_info[field] == '':
            print(f"Trying to read in mykrobe resistance. "
                  f"Field {field} should not be blank. Exiting.")
            sys.exit(1)


def read_in_mykrobe(mykrobe_result_info):
    check_mykrobe_res(mykrobe_result_info)
    mykrobe = Mykrobe()
    mykrobe.mykrobe_version = mykrobe_result_info['mykrobe_version']
    mykrobe.drug = mykrobe_result_info['drug']
    mykrobe.susceptibility = mykrobe_result_info['susceptibility']
    
    if mykrobe_result_info['variants'] != '':
        mykrobe.variants = mykrobe_result_info['variants']
    if mykrobe_result_info['genes'] != '':
        mykrobe.genes = mykrobe_result_info['genes']
    if mykrobe_result_info['phylo_group'] != '':
        mykrobe.phylo_grp = mykrobe_result_info['phylo_group']
    if mykrobe_result_info['species'] != '':
        mykrobe.species = mykrobe_result_info['species']
    if mykrobe_result_info['lineage'] != '':
        mykrobe.lineage = mykrobe_result_info['lineage']
    if mykrobe_result_info['phylo_group_per_covg'] != '':
        mykrobe.phylo_grp_covg = mykrobe_result_info['phylo_group_per_covg']
    if mykrobe_result_info['species_per_covg'] != '':
        mykrobe.species_covg = mykrobe_result_info['species_per_covg']
    if mykrobe_result_info['lineage_per_covg'] != '':
        mykrobe.lineage_covg = mykrobe_result_info['lineage_per_covg']
    if mykrobe_result_info['phylo_group_depth'] != '':
        mykrobe.phylo_grp_depth = mykrobe_result_info['phylo_group_depth']
    if mykrobe_result_info['species_depth'] != '':
        mykrobe.species_depth = mykrobe_result_info['species_depth']
    if mykrobe_result_info['lineage_depth'] != '':
        mykrobe.lineage_depth = mykrobe_result_info['lineage_depth']
    
    return mykrobe


def read_in_tiling_pcr(tiling_pcr_info):
    # doing this earlier in the process now
    # check_tiling_pcr(tiling_pcr_info)
    tiling_pcr = TilingPcr()

    if tiling_pcr_info['date_tiling_pcred']:
        tiling_pcr.date_pcred = tiling_pcr_info['date_tiling_pcred']
    if tiling_pcr_info['tiling_pcr_identifier']:
        tiling_pcr.pcr_identifier = tiling_pcr_info['tiling_pcr_identifier']
    if tiling_pcr_info['tiling_pcr_protocol'] != '':
        tiling_pcr.protocol = tiling_pcr_info['tiling_pcr_protocol']
    if tiling_pcr_info['number_of_cycles'] != '':
        tiling_pcr.number_of_cycles = tiling_pcr_info['number_of_cycles']
    return tiling_pcr


def check_pangolin_result(pangolin_result_info):
    if pangolin_result_info['taxon'].strip() == '':
        print(f'taxon column should not be empty. it is for \n{pangolin_result_info}\nExiting.')
        sys.exit(1)
    if pangolin_result_info['lineage'].strip() == '':
        print(f'lineage column should not be empty. it is for \n{pangolin_result_info}\nExiting.')
        sys.exit(1)
    # the name of the output column changed from status to qc_status 2022-07-04
    if 'qc_status' in pangolin_result_info:
        if 'status' not in pangolin_result_info:
            pangolin_result_info['status'] = pangolin_result_info['qc_status']

    if pangolin_result_info['status'].strip() == '':
        print(f'status column should not be empty. it is for \n{pangolin_result_info}\nExiting.')
        sys.exit(1)


def check_artic_covid_result(artic_covid_result_info):
    if artic_covid_result_info['sample_name'].strip() == '':
        print(f'sample_name column should not be empty. it is for \n{artic_covid_result_info}\nExiting.')
        sys.exit(1)
    if artic_covid_result_info['pct_N_bases'].strip() == '':
        print(f'pct_N_bases column should not be empty. it is for \n{artic_covid_result_info}\nExiting.')
        sys.exit(1)
    if artic_covid_result_info['pct_covered_bases'].strip() == '':
        print(f'pct_covered_bases column should not be empty. it is for \n{artic_covid_result_info}\nExiting.')
        sys.exit(1)
    if artic_covid_result_info['num_aligned_reads'].strip() == '':
        print(f'num_aligned_reads column should not be empty. it is for \n{artic_covid_result_info}\nExiting.')
        sys.exit(1)


def read_in_artic_covid_result(artic_covid_result_info):
    check_artic_covid_result(artic_covid_result_info)
    artic_covid_result = ArticCovidResult()
    artic_covid_result.sample_name = artic_covid_result_info['sample_name']
    artic_covid_result.pct_N_bases = artic_covid_result_info['pct_N_bases']
    artic_covid_result.pct_covered_bases = artic_covid_result_info['pct_covered_bases']
    artic_covid_result.num_aligned_reads = artic_covid_result_info['num_aligned_reads']
    artic_covid_result.workflow = artic_covid_result_info['artic_workflow']
    artic_covid_result.profile = artic_covid_result_info['artic_profile']
    return artic_covid_result


def read_in_pangolin_result(pangolin_result_info):
    check_pangolin_result(pangolin_result_info)
    pangolin_result = PangolinResult()
    pangolin_result.lineage = pangolin_result_info['lineage']
    if pangolin_result_info['conflict'] == '':
        pangolin_result.conflict = None
    else:
        pangolin_result.conflict = pangolin_result_info['conflict']

    if pangolin_result_info['ambiguity_score'] == '':
        pangolin_result.ambiguity_score = None
    else:
        pangolin_result.ambiguity_score = pangolin_result_info['ambiguity_score']

    if pangolin_result_info['scorpio_call'] == '':
        pangolin_result.scorpio_call = None
    else:
        pangolin_result.scorpio_call = pangolin_result_info['scorpio_call']

    if pangolin_result_info['scorpio_support'] == '':
        pangolin_result.scorpio_support = None
    else:
        pangolin_result.scorpio_support = pangolin_result_info['scorpio_support']

    if pangolin_result_info['scorpio_conflict'] == '':
        pangolin_result.scorpio_conflict = None
    else:
        pangolin_result.scorpio_conflict = pangolin_result_info['scorpio_conflict']

    pangolin_result.version = pangolin_result_info['version']
    pangolin_result.pangolin_version = pangolin_result_info['pangolin_version']
    # pangolin_result.pangolearn_version = datetime.datetime.strptime(pangolin_result_info['pangoLEARN_version'], '%Y-%m-%d')
    # pango_version was removed from pangolin v4
    if 'pango_version' in pangolin_result_info:
        pangolin_result.pango_version = pangolin_result_info['pango_version']
    else:
        pangolin_result.pango_version = None
    pangolin_result.status = pangolin_result_info['status']
    pangolin_result.note = pangolin_result_info['note']
    return pangolin_result


def read_in_covid_confirmatory_pcr(covid_confirmatory_pcr_info):
    check_covid_confirmatory_pcr(covid_confirmatory_pcr_info)
    covid_confirmatory_pcr = CovidConfirmatoryPcr()

    if covid_confirmatory_pcr_info['date_covid_confirmatory_pcred']:
        covid_confirmatory_pcr.date_pcred = covid_confirmatory_pcr_info['date_covid_confirmatory_pcred']
    if covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier']:
        covid_confirmatory_pcr.pcr_identifier = covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier']
    if covid_confirmatory_pcr_info['covid_confirmatory_pcr_protocol'] != '':
        covid_confirmatory_pcr.protocol = covid_confirmatory_pcr_info['covid_confirmatory_pcr_protocol']
    if covid_confirmatory_pcr_info['covid_confirmatory_pcr_ct'] == '':
        covid_confirmatory_pcr.ct = None
    else:
        covid_confirmatory_pcr.ct = covid_confirmatory_pcr_info['covid_confirmatory_pcr_ct']
    return covid_confirmatory_pcr


def read_in_pcr_result(pcr_result_info):
    if check_pcr_result(pcr_result_info) is False:
        sys.exit(1)
    pcr_result = PcrResult()

    if pcr_result_info['date_pcred']:
        pcr_result.date_pcred = pcr_result_info['date_pcred']
    if pcr_result_info['pcr_identifier']:
        pcr_result.pcr_identifier = pcr_result_info['pcr_identifier']
    if pcr_result_info['ct'] == '':
        pcr_result.ct = None
    else:
        pcr_result.ct = pcr_result_info['ct']
    if pcr_result_info['pcr_result'] != '':
        pcr_result.pcr_result = pcr_result_info['pcr_result']
    return pcr_result


def add_sample(sample_info, submitted_for_sequencing):
    # sample_info is a dict of one line of the input csv (keys from col header)
    # for the projects listed in the csv, check if they already exist for that group
    # if it does, return it, if it doesnt, instantiate a new Project and return it
    # print(sample_info)
    sample_source = get_sample_source(sample_info)
    if sample_source is False:
        print(f"Adding sample. There is no matching sample_source with the sample_source_identifier "
              f"{sample_info['sample_source_identifier']} for group {sample_info['group_name']}, please add using "
              f"python seqbox_cmd.py add_sample_source and then re-run this command. Exiting.")
        sys.exit(1)
    # instantiate a new Sample
    sample = read_in_sample_info(sample_info)
    sample_source.samples.append(sample)
    sample.submitted_for_sequencing = submitted_for_sequencing
    db.session.add(sample)
    db.session.commit()
    print(f"Adding sample {sample_info['sample_identifier']}")


def rename_dodgy_mykrobe_variables(mykrobe_result_info):
    if 'variants (dna_variant-AA_variant:ref_kmer_count:alt_kmer_count:conf) [use --format json for more info]' in mykrobe_result_info:
        if 'variants' not in mykrobe_result_info:
            mykrobe_result_info['variants'] = mykrobe_result_info['variants (dna_variant-AA_variant:ref_kmer_count:alt_kmer_count:conf) [use --format json for more info]']
    if 'genes (prot_mut-ref_mut:percent_covg:depth) [use --format json for more info]' in mykrobe_result_info:
        if 'genes' not in mykrobe_result_info:
            mykrobe_result_info['genes'] = mykrobe_result_info['genes (prot_mut-ref_mut:percent_covg:depth) [use --format json for more info]']
    return mykrobe_result_info


def add_mykrobe_result(mykrobe_result_info):
    mykrobe_result_info = rename_dodgy_mykrobe_variables(mykrobe_result_info)
    #print(mykrobe_result_info)
    readset = get_readset_from_readset_identifier(mykrobe_result_info)
    if readset is False:
        print(f"Adding mykrobe result. There is no matching readset with the readset_identifier "
              f"{mykrobe_result_info['readset_identifier']}, please add using "
              f"python seqbox_cmd.py add_readset and then re-run this command. Exiting.")
        sys.exit(1)

    mykrobe = read_in_mykrobe(mykrobe_result_info)
    readset.mykrobes.append(mykrobe)
    db.session.add(mykrobe)
    db.session.commit()


def add_sample_source(sample_source_info):
    # sample_info is a dict of one line of the input csv (keys from col header)
    # for the projects listed in the csv, check if they already exist for that group
    # if it does, return it, if it doesnt, instantiate a new Project and return it
    projects = get_projects(sample_source_info)
    # print(projects)
    # instantiate a new SampleSource
    sample_source = read_in_sample_source_info(sample_source_info)
    sample_source.projects = projects
    db.session.add(sample_source)
    db.session.commit()
    print(f'Adding sample_source {sample_source_info["sample_source_identifier"]} to project(s) {projects}')


def add_tiling_pcr(tiling_pcr_info):
    extraction = get_extraction(tiling_pcr_info)
    if extraction is False:
        print(f"Adding tiling PCR. No Extraction match for {tiling_pcr_info['sample_identifier']}, extracted on "
              f"{tiling_pcr_info['date_extracted']} for extraction id {tiling_pcr_info['extraction_identifier']} "
              f"need to add that extract and re-run. Exiting.")
        sys.exit(1)
    tiling_pcr = read_in_tiling_pcr(tiling_pcr_info)
    extraction.tiling_pcrs.append(tiling_pcr)
    db.session.add(tiling_pcr)
    db.session.commit()
    print(f"Adding tiling PCR for sample {tiling_pcr_info['sample_identifier']} run on "
          f"{tiling_pcr_info['date_tiling_pcred']} PCR id {tiling_pcr_info['tiling_pcr_identifier']} to the database.")


def add_covid_confirmatory_pcr(covid_confirmatory_pcr_info):
    extraction = get_extraction(covid_confirmatory_pcr_info)
    if extraction is False:
        print(f"Adding covid confirmatory PCR. "
              f"No Extraction match for {covid_confirmatory_pcr_info['sample_identifier']}, extracted on "
              f"{covid_confirmatory_pcr_info['date_extracted']} for extraction id "
              f"{covid_confirmatory_pcr_info['extraction_identifier']} "
              f"need to add that extract and re-run. Exiting.")
        sys.exit(1)
    covid_confirmatory_pcr = read_in_covid_confirmatory_pcr(covid_confirmatory_pcr_info)
    extraction.covid_confirmatory_pcrs.append(covid_confirmatory_pcr)
    db.session.add(covid_confirmatory_pcr)
    db.session.commit()
    print(f"Adding confirmatory PCR for sample {covid_confirmatory_pcr_info['sample_identifier']} run on "
          f"{covid_confirmatory_pcr_info['date_covid_confirmatory_pcred']} PCR id "
          f"{covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier']} to the database.")


def add_group(group_info):
    group = read_in_group(group_info)
    db.session.add(group)
    db.session.commit()
    print(f"Adding group {group_info['group_name']} from {group_info['institution']} to database.")


def add_pcr_assay(pcr_assay_info):
    pcr_assay = PcrAssay()
    assert pcr_assay_info['assay_name'].strip() != ''
    pcr_assay.assay_name = pcr_assay_info['assay_name']
    db.session.add(pcr_assay)
    db.session.commit()
    print(f"Adding pcr_assay {pcr_assay_info['assay_name']} to database.")


def add_pcr_result(pcr_result_info):
    if check_pcr_result(pcr_result_info) is False:
        sys.exit(1)
    pcr_result = read_in_pcr_result(pcr_result_info)
    assay = get_pcr_assay(pcr_result_info)
    assay.pcr_results.append(pcr_result)
    sample = get_sample(pcr_result_info)
    if sample is False:
        print(f"Adding pcr result, cant find sample for this result:\n{pcr_result_info}\nExiting.")
        sys.exit(1)
    sample.pcr_results.append(pcr_result)
    db.session.add(pcr_result)
    db.session.commit()
    print(f"Adding pcr_result for {pcr_result_info['sample_identifier']}, assay {pcr_result_info['assay_name']} to "
          f"database.")


def add_culture(culture_info):
    sample = get_sample(culture_info)
    if sample is False:
        print(f"Adding culture, cant find sample for this result:\n{culture_info['sample_identifier']} for "
              f"{culture_info['group_name']}\nExiting.")
        sys.exit(1)
    culture = read_in_culture(culture_info)
    sample.cultures.append(culture)
    db.session.add(culture)
    db.session.commit()
    print(f"Adding culture for {culture_info['sample_identifier']} to database.")


def add_extraction(extraction_info):
    extraction = read_in_extraction(extraction_info)
    if extraction_info['extraction_from'] == 'whole_sample':
        sample = get_sample(extraction_info)
        if sample is False:
            print(f"Adding extraction. There is no matching sample with the sample_source_identifier "
                  f"{extraction_info['sample_identifier']} for group {extraction_info['group_name']}, please add using "
                  f"python seqbox_cmd.py add_sample and then re-run this command. Exiting.")
            sys.exit(1)
        sample.extractions.append(extraction)
    elif extraction_info['extraction_from'] == 'cultured_isolate':
        culture = get_culture(extraction_info)
        if culture is False:
            print(f"Adding extraction. There is no matching culture with the sample_source_identifier "
                  f"{extraction_info['sample_identifier']} for group {extraction_info['group_name']}, please add using "
                  f"python seqbox_cmd.py add_culture and then re-run this command. Exiting.")
            sys.exit(1)
        culture.extractions.append(extraction)
    db.session.add(extraction)
    db.session.commit()
    print(f"Adding {extraction_info['sample_identifier']} extraction on {extraction_info['date_extracted']} to the DB")


def add_elution_info_to_extraction(elution_info):
    extraction = get_extraction(elution_info)
    if extraction is False:
        print(f"Adding elution info. "
              f"No Extraction match for {elution_info['sample_identifier']}, extracted on "
              f"{elution_info['date_extracted']} for extraction id "
              f"{elution_info['extraction_identifier']} "
              f"need to add that extract and re-run. Exiting.")
        sys.exit(1)
    assert elution_info['elution_plate_well'] in {'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10',
                                                    'A11', 'A12', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8',
                                                    'B9', 'B10', 'B11', 'B12', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6',
                                                    'C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'D1', 'D2', 'D3', 'D4',
                                                    'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12', 'E1', 'E2',
                                                    'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12',
                                                    'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10',
                                                    'F11', 'F12', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8',
                                                    'G9', 'G10', 'G11', 'G12', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
                                                    'H7', 'H8', 'H9', 'H10', 'H11', 'H12'}
    extraction.elution_plate_id = elution_info['elution_plate_id']
    extraction.elution_plate_well = elution_info['elution_plate_well']
    #elution = read_in_elution(elution_info)
    #extraction.elutions.append(elution)
    #db.session.add(elution)
    db.session.commit()
    print(f"Adding elution info for {elution_info['sample_identifier']} extraction on "
          f"{elution_info['date_extracted']} to the DB")

def get_tiling_pcr(tiling_pcr_info):
    matching_tiling_pcr = TilingPcr.query\
        .filter_by(
            pcr_identifier=tiling_pcr_info['tiling_pcr_identifier'],

            date_pcred=tiling_pcr_info['date_tiling_pcred'])\
        .join(Extraction).join(Sample).filter_by(sample_identifier=tiling_pcr_info['sample_identifier']).all()
    if len(matching_tiling_pcr) == 1:
        return matching_tiling_pcr[0]
    elif len(matching_tiling_pcr) == 0:
        return False
    else:
        print(f"Getting tiling PCR. More than one match for {tiling_pcr_info['sample_identifier']} on date "
              f"{tiling_pcr_info['date_tiling_pcred']} "
              f"with pcr_identifier {tiling_pcr_info['tiling_pcr_identifier']}. Shouldn't happen, exiting.")
        sys.exit(1)


def get_covid_confirmatory_pcr(covid_confirmatory_pcr_info):
    matching_covid_confirmatory_pcr = CovidConfirmatoryPcr.query.filter_by(
        pcr_identifier=covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier'],

        date_pcred=covid_confirmatory_pcr_info['date_covid_confirmatory_pcred'] )\
        .join(Extraction).filter_by(extraction_identifier=covid_confirmatory_pcr_info['extraction_identifier'],
                                                     date_extracted=datetime.datetime.strptime(
                                                         covid_confirmatory_pcr_info['date_extracted'], '%d/%m/%Y')) \
        .join(Sample).filter_by(sample_identifier=covid_confirmatory_pcr_info['sample_identifier'])\
        .all()
    if len(matching_covid_confirmatory_pcr) == 0:
        return False
    elif len(matching_covid_confirmatory_pcr) == 1:
        return matching_covid_confirmatory_pcr[0]
    else:
        print(f"Getting covid confirmatory PCR. "
              f"More than one match for {covid_confirmatory_pcr_info['sample_identifier']} on date"
              f" {covid_confirmatory_pcr_info['date_covid_confirmatory_pcred']} with covid_confirmatory_pcr_identifier "
              f"{covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier']}. Shouldn't happen, exiting.")
        sys.exit(1)


def get_pcr_assay(pcr_assay_info):
    # matching_pcr_result = PcrResult
    matching_pcr_assay = PcrAssay.query.filter_by(assay_name=pcr_assay_info['assay_name']).all()
    if len(matching_pcr_assay) == 0:
        return False
    elif len(matching_pcr_assay) == 1:
        return matching_pcr_assay[0]
    else:
        print(f"Getting pcr assay. Within getting pcr_result. "
              f"More than one match in the db for {pcr_assay_info['assay']}. "
              f"Shouldn't happen, exiting.")
        sys.exit(1)


def get_pcr_result(pcr_result_info):
    assay = get_pcr_assay(pcr_result_info)
    if assay is False:
        print(f"There is no pcr assay called {pcr_result_info['assay_name']} in the database, please add it and re-run. "
              f"Exiting.")
        sys.exit(1)
    matching_pcr_result = PcrResult.query.filter_by(
                                                    date_pcred=pcr_result_info['date_pcred'],
                                                    pcr_identifier=pcr_result_info['pcr_identifier'])\
        .join(PcrAssay).filter_by(assay_name=pcr_result_info['assay_name'])\
        .join(Sample).filter_by(sample_identifier=pcr_result_info['sample_identifier']).all()
    if len(matching_pcr_result) == 0:
        return False
    elif len(matching_pcr_result) == 1:
        return matching_pcr_result[0]
    else:
        print(f"Getting pcr result."
              f"More than one match in the db for {pcr_result_info['sample_identifier']}, running the "
              f"{pcr_result_info['assay']} test, on {pcr_result_info['date_pcred']} "
              f"Shouldn't happen, exiting.")
        sys.exit(1)


def get_readset_batch(readset_batch_info):
    matching_readset_batch = ReadSetBatch.query.filter_by(name=readset_batch_info['readset_batch_name']).all()
    if len(matching_readset_batch) == 0:
        return False
    elif len(matching_readset_batch) == 1:
        return matching_readset_batch[0]
    else:
        print(f"Getting readset batch. "
              f"More than one match for {readset_batch_info['readset_batch_name']}. "
              f"Shouldn't happen, exiting.")
        sys.exit(1)


def get_group(group_info):
    matching_group = Groups.query.filter_by(group_name=group_info['group_name'], institution=group_info['institution'])\
        .all()
    if len(matching_group) == 0:
        return False
    elif len(matching_group) == 1:
        return matching_group[0]
    else:
        print(f"Getting group. "
              f"More than one match for {group_info['group_name']} from {group_info['institution']}. Shouldn't happen, "
              f"exiting.")
        sys.exit(1)


def get_readset_from_readset_identifier(readset_info):
    matching_readset = ReadSet.query.filter_by(readset_identifier=readset_info['readset_identifier']).all()
    if len(matching_readset) == 0:
        return False
    elif len(matching_readset) == 1:
        return matching_readset[0]
    else:
        print(f"Getting readset. "
              f"More than one match for {readset_info['readset_identifier']}. Shouldn't happen, exiting.")
        sys.exit(1)


def get_readset(readset_info, covid):
    # first we get the readset batch so that we can get the raw sequencing batch so that we can get the sequencing type
    readset_batch = get_readset_batch(readset_info)
    if readset_batch is False:
        print(
            f"Getting readset. No ReadSetBatch match for {readset_info['readset_batch_name']}, need to add that batch "
            f"and re-run. Exiting.")
        sys.exit(1)
    # this get_raw_sequencing_batch is probably superfluous, because the readset_batch should be guaranteed to have
    #  a raw_seuqencing_batch attribute, and can then just be replaced with an assertion that it's true
    #  but will leave it in for now.
    # assert isinstance(readset_batch.raw_sequencing_batch, RawSequencingBatch)
    # then,  we need to get the batch to see what kind of sequencing it is
    raw_sequencing_batch = get_raw_sequencing_batch(readset_batch.raw_sequencing_batch.name)
    if raw_sequencing_batch is False:
        print(
            f"Getting readset. No RawSequencingBatch match for {readset_info['readset_batch_name']}, "
            f"need to add that batch and re-run. Exiting.")
        sys.exit(1)

    readset_type = None
    # this is because the readset query is currently generic to sequencing type, so we use this structure to
    #  cut down on duplicate code (otherwise, would need all of the below for both illumina and nanopore).
    # can probably just do this with readset_batch.raw_sequencing_batch.sequencing_type == 'illumina'
    if raw_sequencing_batch.sequencing_type == 'illumina':
        readset_type = ReadSetIllumina
    elif raw_sequencing_batch.sequencing_type == 'nanopore':
        readset_type = ReadSetNanopore
    # todo - is this going to be a slow query when readset_ill/nano get big?
    # if the sample isnt covid, then need to match against the extraciton
    # todo - none of the tests here are actually for readset, they're all for rsb and above.
    # to cover new basecalling runs of same raw sequencing, need to test for whether the fastq is already in the
    # database.
    # so - if it's nanopore default, need to construct the fastq path from rsb.batch_dir, barcode, fastq
    #  (should spin out the get fastq path functionality from add readset to filesystem into sep func)
    # if it's nanopore, but not default, the fastq path will be in the readset_info.
    # then, if it's nanopore, then filter the read_set_nanopore by the fastq path.

    # todo - replace these combined queries with a union query going through tiling pcr for COVID, and then can get
    # rid of the covid flag for this function (i think).
    if covid is False:
        matching_readset = readset_type.query.join(ReadSet)\
            .join(ReadSetBatch).filter_by(name=readset_info['readset_batch_name'])\
            .join(RawSequencing) \
            .join(Extraction).filter_by(
                                        date_extracted=readset_info['date_extracted'],
                                        extraction_identifier=readset_info['extraction_identifier'])\
            .filter(Extraction.submitter_plate_id.is_not(None)) \
            .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier'])\
            .join(SampleSource)\
            .join(SampleSource.projects) \
            .join(Groups)\
            .filter_by(group_name=readset_info['group_name'])\
            .distinct().union(readset_type.query
                              .join(ReadSet)
                              .join(ReadSetBatch).filter_by(name=readset_info['readset_batch_name']) \
                              .join(RawSequencing)
                              .join(Extraction)
                              .filter_by(
                                         date_extracted=readset_info['date_extracted'],
                                         extraction_identifier=readset_info['extraction_identifier'])
                              .join(Culture).filter(Culture.submitter_plate_id.is_not(None)) \
                              .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier']) \
                              .join(SampleSource).join(SampleSource.projects) \
                              .join(Groups).filter_by(group_name=readset_info['group_name']) \
                              .distinct()).all()
    # if the sample is covid, then need to match against the tiling pcr
    elif covid is True:
        matching_readset = readset_type.query.join(ReadSet)\
            .join(ReadSetBatch).filter_by(name=readset_info['readset_batch_name']) \
            .join(RawSequencing) \
            .join(TilingPcr).filter_by(
                                        date_pcred=readset_info['date_tiling_pcred'],
                                       pcr_identifier=readset_info['tiling_pcr_identifier']) \
            .join(Extraction)\
            .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier']) \
            .join(SampleSource) \
            .join(SampleSource.projects) \
            .join(Groups) \
            .filter_by(group_name=readset_info['group_name']) \
            .distinct().all()
    # if there is no matching readset, return False
    if len(matching_readset) == 0:
        return False
    elif len(matching_readset) == 1:
        return matching_readset[0]
    else:
        print(f"Getting readset. More than one match for {readset_info['readset_batch_name']}. "
              f"Shouldn't happen, exiting.")
        sys.exit(1)


def read_in_raw_sequencing_batch_info(raw_sequencing_batch_info):
    check_raw_sequencing_batch(raw_sequencing_batch_info)
    raw_sequencing_batch = RawSequencingBatch()
    raw_sequencing_batch.name = raw_sequencing_batch_info['batch_name']

    raw_sequencing_batch.date_run = raw_sequencing_batch_info['date_run']
    raw_sequencing_batch.instrument_model = raw_sequencing_batch_info['instrument_model']
    raw_sequencing_batch.instrument_name = raw_sequencing_batch_info['instrument_name']
    raw_sequencing_batch.sequencing_centre = raw_sequencing_batch_info['sequencing_centre']
    raw_sequencing_batch.flowcell_type = raw_sequencing_batch_info['flowcell_type']
    raw_sequencing_batch.sequencing_type = raw_sequencing_batch_info['sequencing_type']
    raw_sequencing_batch.batch_directory = raw_sequencing_batch_info['batch_directory']
    return raw_sequencing_batch


def read_in_readset_batch(readset_batch_info):
    check_readset_batches(readset_batch_info)
    readset_batch = ReadSetBatch()
    readset_batch.name = readset_batch_info['readset_batch_name']
    readset_batch.batch_directory = readset_batch_info['readset_batch_dir']
    readset_batch.basecaller = readset_batch_info['basecaller']
    return readset_batch


def add_raw_sequencing_batch(raw_sequencing_batch_info):
    raw_sequencing_batch = read_in_raw_sequencing_batch_info(raw_sequencing_batch_info)
    db.session.add(raw_sequencing_batch)
    db.session.commit()
    print(f"Added raw sequencing batch {raw_sequencing_batch_info['batch_name']} to the database.")


def get_raw_sequencing_batch(batch_name):
    matching_raw_seq_batch = RawSequencingBatch.query.filter_by(name=batch_name).all()
    if len(matching_raw_seq_batch) == 1:
        return matching_raw_seq_batch[0]
    elif len(matching_raw_seq_batch) == 0:
        return False
    else:
        print(f"Getting raw_sequencing batch. More than one match for {batch_name}. Shouldn't happen, exiting.")
        sys.exit(1)


def get_raw_sequencing(readset_info, raw_sequencing_batch, covid):
    if covid is True:
        matching_raw_sequencing = RawSequencing.query \
            .join(RawSequencingBatch).filter_by(name=raw_sequencing_batch.name) \

            .join(TilingPcr).filter_by(pcr_identifier=readset_info['tiling_pcr_identifier'],
                                       date_pcred=datetime.datetime \
                                       .strptime(readset_info['date_tiling_pcred'], '%d/%m/%Y')) \
            .join(Extraction) \
            .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier']) \
            .join(SampleSource) \
            .join(SampleSource.projects)\
            .join(Groups) \
            .filter_by(group_name=readset_info['group_name']) \
            .all()
    elif covid is False:
        matching_raw_sequencing = RawSequencing.query \
            .join(RawSequencingBatch).filter_by(name=raw_sequencing_batch.name) \
            .join(Extraction)\

            .filter_by(date_extracted=readset_info['date_extracted'],
                       extraction_identifier=readset_info['extraction_identifier']) \
            .filter(Extraction.submitter_plate_id.is_not(None)) \
            .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier']) \
            .join(SampleSource) \
            .join(SampleSource.projects) \
            .join(Groups) \
            .filter_by(group_name=readset_info['group_name']) \
            .distinct().union(RawSequencing.query
                              .join(RawSequencingBatch).filter_by(name=raw_sequencing_batch.name) \
                              .join(Extraction)

                              .filter_by(date_extracted=readset_info['date_extracted'],
                                         extraction_identifier=readset_info['extraction_identifier'])
                              .join(Culture).filter(Culture.submitter_plate_id.is_not(None)) \
                              .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier']) \
                              .join(SampleSource).join(SampleSource.projects) \
                              .join(Groups).filter_by(group_name=readset_info['group_name']) \
                              .distinct()).all()
    if len(matching_raw_sequencing) == 0:
        # no matching raw sequencing will be the case for 99.999% of illumina (all illumina?) and most nanopore
        return False
    elif len(matching_raw_sequencing) == 1:
        # if there is already a raw_sequencing record (i.e. this is another basecalling run of the same raw_sequencing
        # data), then extraction is already assocaited with the raw sequencing, so don't need to add.
        # todo - add in asserts checking that thing returning matches the queries in order to guard against shittly
        #  written queries
        # assert matching_raw_sequencing[0].tiling_pcr.tiling_pcr_identifier == readset_info['tiling_pcr_identifier']
        # assert matching_raw_sequencing[0].tiling_pcr.date_pcred == readset_info['date_tiling_pcred']
        # assert matching_raw_sequencing[0].extraction.sample.sample_identifier == readset_info['sample_identifier']
        # assert matching_raw_sequencing[0].extraction.sample.projects.group_name == readset_info['group_name']
        return matching_raw_sequencing[0]
    else:
        print(f"Getting raw_sequencing, more than one match in {readset_info['batch']} for sample "
              f"{readset_info['sample_identifier']} from group {readset_info['group_name']}. This shouldn't happen.")

# def find_submitter_plate(sample):
#     if sample.


def query_info_on_all_samples(args):
    # at the moment args just being passed through in case needs to be used in future
    # need to use the sqlalchemy native option rather than the flask-sqlalchemy option as the latter doesn't nicely
    # return the join, have to do it manually from the results (?i think?)
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    # from here https://stackoverflow.com/questions/43459182/proper-sqlalchemy-use-in-flask
    engine = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    s = Session()
    # need to do a union query to get samples from both the sample-culture-extract, sample-extract paths, and
    # just samples (i.e. whole samples submitted for extraction).
    #
    # the filter(Culture.submitter_plate_id.is_not(None)) and filter(Extraction.submitter_plate_id.is_not(None))
    # are to ensure that samples from the other path are not included in the results of the query (i.e. samples that are
    # None for Culture.submitter_plate_id will be ones where the submitter gave in extracts, and that hence so sample-extract).
    sample_culture_extract = s.query(Sample, Groups.group_name, Groups.institution, Project.project_name, Sample.sample_identifier, Sample.species, Sample.sequencing_type_requested, Culture.submitter_plate_id, Culture.submitter_plate_well,
                     Extraction.elution_plate_id, Extraction.elution_plate_well, Extraction.date_extracted, Extraction.extraction_identifier, Extraction.nucleic_acid_concentration, ReadSet.readset_identifier) \
        .join(SampleSource)\
        .join(SampleSource.projects)\
        .join(Groups) \
        .join(Culture, isouter=True).filter(Culture.submitter_plate_id.is_not(None)) \
        .join(Extraction, isouter=True) \
        .join(RawSequencing, isouter=True) \
        .join(ReadSet, isouter=True)
    #samples = [r._asdict() for r in samples]
    sample_extract = s.query(Sample, Groups.group_name, Groups.institution, Project.project_name,
                             Sample.sample_identifier, Sample.species, Sample.sequencing_type_requested,
                             Extraction.submitter_plate_id, Extraction.submitter_plate_well,
                             Extraction.elution_plate_id, Extraction.elution_plate_well, Extraction.date_extracted,
                             Extraction.extraction_identifier, Extraction.nucleic_acid_concentration,
                             ReadSet.readset_identifier)\
        .join(SampleSource)\
        .join(SampleSource.projects)\
        .join(Groups) \
        .join(Extraction, isouter=True).filter(Extraction.submitter_plate_id.is_not(None)) \
        .join(RawSequencing, isouter=True) \
        .join(ReadSet, isouter=True)

    sample = s.query(Sample, Groups.group_name, Groups.institution, Project.project_name,
                             Sample.sample_identifier, Sample.species, Sample.sequencing_type_requested,
                             Sample.submitter_plate_id, Sample.submitter_plate_well,
                             Extraction.elution_plate_id, Extraction.elution_plate_well, Extraction.date_extracted,
                             Extraction.extraction_identifier, Extraction.nucleic_acid_concentration,
                             ReadSet.readset_identifier) \
        .filter(Sample.submitter_plate_id.is_not(None))        \
        .join(SampleSource) \
        .join(SampleSource.projects) \
        .join(Groups) \
        .join(Extraction, isouter=True) \
        .join(RawSequencing, isouter=True) \
        .join(ReadSet, isouter=True)

    union_of_both = sample_culture_extract.union(sample_extract).union(sample).all()

    header = ['group_name', 'institution', 'project_name', 'sample_identifier', 'species', 'sequencing_type_requested', 'submitter_plate_id', 'submitter_plate_well', 'elution_plate_id', 'elution_plate_well', 'date_extracted', 'extraction_identifier', 'nucleic_acid_concentration', 'readset_identifier']
    print('\t'.join(header))
    for x in union_of_both:
        # check that the header is the same length as each return of the query
        # this is in case we add something to the return, but forget to add it to the header
        # we add 1 to the length of the header return because the first element of x is the sample object, which we
        # don't print
        assert len(header) +1 == len(x)
        # replace the Nones with empty strings because want to use the output as the input for a future upload and the
        # Nones will cause problems
        x = ['' if y is None else y for y in x]
        #print(type(x[9]))
        # want to get the date, not the datetime.
        if not x[9] == '':
            x[9] = x[9].date()
        print('\t'.join([str(y) for y in x[1:]]))
    s.close()


def read_in_raw_sequencing(readset_info, nanopore_default, sequencing_type, batch_directory):
    raw_sequencing = RawSequencing()
    if sequencing_type == 'illumina':
        raw_sequencing.raw_sequencing_illumina = RawSequencingIllumina()
        # not taking the read paths from the input file anymore, will get them from the inbox_from_config/batch/sample_name
        #raw_sequencing.raw_sequencing_illumina.path_r1 = readset_info['path_r1']
        #raw_sequencing.raw_sequencing_illumina.path_r2 = readset_info['path_r2']
        # if the readset is externally sequenced, then the submitter_readset_id will start with OUT, and
        # we don't want to add the library prep method
        if not readset_info['submitter_plate_id'].startswith('OUT'):
            raw_sequencing.raw_sequencing_illumina.library_prep_method = readset_info['library_prep_method']
    if sequencing_type == 'nanopore':
        raw_sequencing.raw_sequencing_nanopore = RawSequencingNanopore()
        if nanopore_default is True:
            path = os.path.join(batch_directory, 'fast5_pass', readset_info['barcode'], '*fast5')
            raw_sequencing.raw_sequencing_nanopore.path_fast5 = path
            raw_sequencing.raw_sequencing_nanopore.library_prep_method = readset_info['library_prep_method']
            fast5s = glob.glob(path)
            if len(fast5s) == 0:
                print(f'Warning - No fast5 found in {path}. Continuing, but check this.')
        elif nanopore_default is False:
            assert readset_info['path_fast5'].endswith('fast5')
            assert os.path.isfile(readset_info['path_fast5'])
            raw_sequencing.raw_sequencing_nanopore.path_fast5 = readset_info['path_fast5']
        # raw_sequencing.raw_sequencing_nanopore.append(raw_sequencing_nanopore)
    return raw_sequencing


def check_raw_sequencing_batch(raw_sequencing_batch_info):
    if raw_sequencing_batch_info['batch_directory'].strip() == '':
        print(f'batch_directory column should not be empty. it is for \n{raw_sequencing_batch_info}\nExiting.')
        sys.exit(1)
    if raw_sequencing_batch_info['batch_name'].strip() == '':
        print(f'batch_name column should not be empty. it is for \n{raw_sequencing_batch_info}\nExiting.')
        sys.exit(1)
    if raw_sequencing_batch_info['date_run'].strip() == '':
        print(f'date_run column should not be empty. it is for \n{raw_sequencing_batch_info}\nExiting.')
        sys.exit(1)
    if raw_sequencing_batch_info['sequencing_type'].strip() == '':
        print(f'sequencing_type column should not be empty. it is for \n{raw_sequencing_batch_info}\nExiting.')
        sys.exit(1)
    if raw_sequencing_batch_info['instrument_name'].strip() == '':
        print(f'batch_directory column should not be empty. it is for \n{raw_sequencing_batch_info}\nExiting.')
        sys.exit(1)

    if raw_sequencing_batch_info['flowcell_type'].strip() == '':
        print(f'date_run column should not be empty. it is for \n{raw_sequencing_batch_info}\nExiting.')
        sys.exit(1)


def check_readset_batches(readset_batch_info):
    if readset_batch_info['raw_sequencing_batch_name'].strip() == '':
        print(f'raw_sequencing_batch_name column should not be empty. it is for \n{readset_batch_info}\nExiting.')
        sys.exit(1)
    if readset_batch_info['readset_batch_name'].strip() == '':
        print(f'readset_batch_name column should not be empty. it is for \n{readset_batch_info}\nExiting.')
        sys.exit(1)
    if readset_batch_info['readset_batch_dir'].strip() == '':
        print(f'readset_batch_dir column should not be empty. it is for \n{readset_batch_info}\nExiting.')
        sys.exit(1)
    if readset_batch_info['basecaller'].strip() == '':
        print(f'basecaller column should not be empty. it is for \n{readset_batch_info}\nExiting.')
        sys.exit(1)


def check_cultures(culture_info):
    if (culture_info['culture_identifier'].strip() == '') and (culture_info['date_cultured'].strip() == ''):
        print(f'There is no culture information fo this sample - {culture_info["sample_identifier"]}. Continuing.')
        return False
    elif (culture_info['culture_identifier'].strip() != '') and (culture_info['date_cultured'].strip() != ''):
        return True
    else:
        print(f'date_cultured and culture_identifier column should not both be empty. '
              f'it is for \n{culture_info}\nExiting.')
        sys.exit()
    # we assert that the submitter plate is for cultures or, if the client submitted extracts from a culture,
    # that the extraction_from is cultured_isolate
    # if the readset was sequenced elsewhere,  the submitter_plate_id will start with OUT
    assert culture_info['submitter_plate_id'].startswith('CUL') or \
           culture_info['extraction_from'] == 'cultured_isolate' or \
           culture_info['submitter_plate_id'].startswith('OUT')
    assert culture_info['submitter_plate_well'] in {'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10',
                                                       'A11', 'A12', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8',
                                                       'B9', 'B10', 'B11', 'B12', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6',
                                                       'C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'D1', 'D2', 'D3', 'D4',
                                                       'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12', 'E1', 'E2',
                                                       'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12',
                                                       'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10',
                                                       'F11', 'F12', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8',
                                                       'G9', 'G10', 'G11', 'G12', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6',
                                                       'H7', 'H8', 'H9', 'H10', 'H11', 'H12'}


def check_extraction_fields(extraction_info):

    """ This function should:
     1. return True if all extraction fields are present
     2. return False if all fields are blank
     3. sys.exit if some extraction fields are not present
    """

    extraction_info_values = extraction_info.values()
    # Check if all columns are blank i.e contain None

    extraction_info_blank = all(e_value is None for e_value in extraction_info_values)
    if extraction_info_blank is True:
        print("Warning:all columns are blank")
        return False

    # Check individual columns if they are blank

    if not extraction_info['sample_identifier']:
        print(f'sample_identifier column should not be empty. it is for \n{extraction_info}\nExiting.')
        sys.exit(1)


    if not extraction_info['date_extracted']:

        print(f'date_extracted column should not be empty. it is for \n{extraction_info}\nExiting.')
        sys.exit(1)


    if not (extraction_info['extraction_identifier']):
        print(f'extraction_identifier column should not be empty. it is for \n{extraction_info}\nExiting.')
        sys.exit(1)


    if not extraction_info['group_name']:
        print(f'extraction_identifier column should not be empty. it is for \n{extraction_info}\nExiting.')
        sys.exit(1)


    if not extraction_info['extraction_from']:
        print(f'extraction_from column should not be empty. it is for \n{extraction_info}\nExiting.')
        sys.exit(1)


    allowed_extraction_from = ['cultured_isolate', 'whole_sample']
    if extraction_info['extraction_from'] not in allowed_extraction_from:
        print(f'extraction_from column must be one of {allowed_extraction_from}, it is not for \n{extraction_info}\n. '
            f'Exiting.')
        sys.exit(1)


    if not (extraction_info['nucleic_acid_concentration']):
        print(f'nucleic_acid_concentration column should not be empty. it is for \n{extraction_info}\nExiting.')
        sys.exit(1)


    allowed_submitter_plate_prefixes = ('EXT', 'CUL')
    if not extraction_info['submitter_plate_id'].startswith(allowed_submitter_plate_prefixes):
       print(f'submitter_plate_id column should start with one of {allowed_submitter_plate_prefixes}. it doesnt for \n{extraction_info}\nExiting.')
       sys.exit(1)


    if extraction_info['submitter_plate_well'] not in {'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12', 'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12', 'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12', 'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12', 'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12', 'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12', 'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10', 'G11', 'G12', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11', 'H12'}:
        sys.exit(1)
    return True

    # if the lab guys have done the extraction from a culture, there might not be an submitter



def check_group(group_info):
    if ' ' in group_info['group_name']:
        print(f'group_name should not have any spaces in in. there is one for \n{group_info}\nExiting.')
        sys.exit(1)
    if '/' in group_info['group_name']:
        print(f'group_name should not have any backslashes in in. there is one for \n{group_info}\nExiting.')
        sys.exit(1)
    if group_info['group_name'].strip() == '':
        print(f'group_name column should not be empty. it is for \n{group_info}\nExiting.')
        sys.exit(1)
    if group_info['institution'].strip() == '':
        print(f'institution column should not be empty. it is for \n{group_info}\nExiting.')
        sys.exit(1)


def check_project(project_info):
    if project_info['project_name'].strip() == '':
        print(f'project_name column should not be empty. it is for \n{project_info}\nExiting.')
        sys.exit(1)
    if project_info['group_name'].strip() == '':
        print(f'group_name column should not be empty. it is for \n{project_info}\nExiting.')
        sys.exit(1)
    if project_info['institution'].strip() == '':
        print(f'institution column should not be empty. it is for \n{project_info}\nExiting.')
        sys.exit(1)


def check_sample_sources(sample_source_info):
    if sample_source_info['sample_source_identifier'].strip() == '':
        print(f'sample_source_identifier column should not be empty. it is for \n{sample_source_info}\nExiting.')
        sys.exit(1)
    if sample_source_info['sample_source_type'].strip() == '':
        print(f'sample_source_type column should not be empty. it is for \n{sample_source_info}\nExiting.')
        sys.exit(1)
    if sample_source_info['projects'].strip() == '':
        print(f'projects column should not be empty. it is for \n{sample_source_info}\nExiting.')
        sys.exit(1)
    if sample_source_info['group_name'].strip() == '':
        print(f'group_name column should not be empty. it is for \n{sample_source_info}\nExiting.')
        sys.exit(1)
    if sample_source_info['institution'].strip() == '':
        print(f'institution column should not be empty. it is for \n{sample_source_info}\nExiting.')
        sys.exit(1)


def check_samples(sample_info):
    if sample_info['sample_source_identifier'].strip() == '':
        print(f'sample_source_identifier column should not be empty. it is for \n{sample_info}\nExiting.')
        sys.exit(1)
    if sample_info['sample_identifier'].strip() == '':
        print(f'sample_identifier column should not be empty. it is for \n{sample_info}\nExiting.')
        sys.exit(1)
    if sample_info['group_name'].strip() == '':
        print(f'group_name column should not be empty. it is for \n{sample_info}\nExiting.')
        sys.exit(1)
    if sample_info['institution'].strip() == '':
        print(f'institution column should not be empty. it is for \n{sample_info}\nExiting.')
        sys.exit(1)


def check_covid_confirmatory_pcr(covid_confirmatory_pcr_info):
    if covid_confirmatory_pcr_info['sample_identifier'].strip() == '':
        print(f'sample_identifier column should not be empty. it is for \n{covid_confirmatory_pcr_info}\nExiting.')
        sys.exit(1)
    if covid_confirmatory_pcr_info['date_extracted'].strip() == '':
        print(f'date_extracted column should not be empty. it is for \n{covid_confirmatory_pcr_info}\nExiting.')
        sys.exit(1)
    if covid_confirmatory_pcr_info['extraction_identifier'].strip() == '':
        print(f'extraction_identifier column should not be empty. it is for \n{covid_confirmatory_pcr_info}\nExiting.')
        sys.exit(1)
    if covid_confirmatory_pcr_info['date_covid_confirmatory_pcred'].strip() == '':
        print(f'date_covid_confirmatory_pcred column should not be empty. it is for '
              f'\n{covid_confirmatory_pcr_info}\nExiting.')
        sys.exit(1)
    if covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier'].strip() == '':
        print(f'covid_confirmatory_pcr_identifier column should not be empty. it is for '
              f'\n{covid_confirmatory_pcr_info}\nExiting.')
        sys.exit(1)
    if covid_confirmatory_pcr_info['group_name'].strip() == '':
        print(f'group_name column should not be empty. it is for \n{covid_confirmatory_pcr_info}\nExiting.')
        sys.exit(1)
    if covid_confirmatory_pcr_info['covid_confirmatory_pcr_protocol'].strip() == '':
        print(f'covid_confirmatory_pcr_protocol column should not be empty. it is for \n{covid_confirmatory_pcr_info}\nExiting.')
        sys.exit(1)


def check_tiling_pcr(tiling_pcr_info):
    to_check = ['sample_identifier', 'date_extracted', 'extraction_identifier', 'date_tiling_pcred',
                'tiling_pcr_identifier', 'group_name', 'tiling_pcr_protocol']
    for r in to_check:
        if tiling_pcr_info[r].strip() == '':
            print(f'Warning - {r} column should not be empty. it is for \n{tiling_pcr_info}. Not adding this tiling pcr record.')
            return False
    return True


def check_pcr_result(pcr_result_info):
    to_check = ['sample_identifier', 'date_pcred', 'pcr_identifier', 'group_name', 'assay_name']
    for r in to_check:
        if pcr_result_info[r].strip() == '':
            print(f'{r} column should not be empty. it is for \n{pcr_result_info}')
            return False

    allowable_results = {'Negative', 'Negative - Followup', 'Positive - Followup', 'Positive',
                         'Indeterminate', 'Not Done'}
    if pcr_result_info['pcr_result'] not in allowable_results:
        print(f'result column should contain one of these results {allowable_results}. '
              f'it doesnt for \n{pcr_result_info}\nExiting.')
        sys.exit(1)


def basic_check_readset_fields(readset_info):
    # need two flavours of check read set fields, this one is to not try and make a readset record when
    # it looks like the readset is totally missing, which would be the case in teh combined input file if the
    # covid confirmatory pcr was negative.
    to_check = ['data_storage_device', 'readset_batch_name']
    for r in to_check:
        if readset_info[r].strip() == '':
            print(f'Warning - {r} column should not be empty. it is for \n{readset_info}.')
            return False


def check_readset_fields(readset_info, nanopore_default, raw_sequencing_batch, covid):
    # this is the full check of the readset fields, when it looks like the readset is present.
    to_check = ['data_storage_device', 'sample_identifier', 'group_name', 'readset_batch_name']
    for r in to_check:
        if readset_info[r].strip() == '':
            print(f'{r} column should not be empty. it is for \n{readset_info}\nExiting.')
            sys.exit()

    if raw_sequencing_batch.sequencing_type == 'nanopore':
        if nanopore_default is True:
            if readset_info['barcode'].strip() == '':
                print(f'barcode column should not be empty. it is for \n{readset_info}\nExiting.')
                sys.exit(1)
        else:
            if readset_info['path_fastq'].strip() == '':
                print(f'path_fastq column should not be empty. it is for \n{readset_info}\nExiting.')
                sys.exit(1)
            if readset_info['path_fast5'].strip() == '':
                print(f'path_fast5 column should not be empty. it is for \n{readset_info}\nExiting.')
                sys.exit(1)
    # not taking the read paths from the input file anymore, will get them from the inbox_from_config/batch/sample_name
    # elif raw_sequencing_batch.sequencing_type == 'illumina':
    #     if not readset_info['path_r1']:
    #         print(f'path_r1 column should not be empty. it is for \n{readset_info}\nExiting.')
    #         sys.exit(1)
    #     if not readset_info['path_r2']:
    #         print(f'path_r2 column should not be empty. it is for \n{readset_info}\nExiting.')
    #         sys.exit(1)
    if covid is True:
        if readset_info['date_tiling_pcred'].strip() == '':
            print(f'date_tiling_pcred column should not be empty. it is for \n{readset_info}\nExiting.')
            sys.exit(1)
        if readset_info['tiling_pcr_identifier'].strip() == '':
            print(f'tiling_pcr_identifier column should not be empty. it is for \n{readset_info}\nExiting.')
            sys.exit(1)
    else:
        if readset_info['date_extracted'].strip() == '':
            print(f'date_extracted column should not be empty. it is for \n{readset_info}\nExiting.')
            sys.exit(1)
        if readset_info['extraction_identifier'].strip() == '':
            print(f'extraction_identifier column should not be empty. it is for \n{readset_info}\nExiting.')
            sys.exit(1)


def read_in_readset(readset_info, nanopore_default, raw_sequencing_batch, readset_batch, covid):
    readset = ReadSet()
    check_readset_fields(readset_info, nanopore_default, raw_sequencing_batch, covid)

    readset.data_storage_device = readset_info['data_storage_device']
    if raw_sequencing_batch.sequencing_type == 'nanopore':
        readset.readset_nanopore = ReadSetNanopore()
        if nanopore_default is False:
            assert readset_info['path_fastq'].endswith('fastq.gz')
            readset.readset_nanopore.path_fastq = readset_info['path_fastq']
        elif nanopore_default is True:
            readset.readset_nanopore.barcode = readset_info['barcode']
            path = os.path.join(readset_batch.batch_directory, 'fastq_pass', readset_info['barcode'], '*fastq.gz')
            fastqs = glob.glob(path)
            if len(fastqs) == 1:
                readset.readset_nanopore.path_fastq = fastqs[0]
            elif len(fastqs) == 0:
                print(f'Reading in readset. No fastq found in {path}. Exiting.')
                sys.exit(1)
            elif len(fastqs) > 1:
                print(f'Reading in readset. More than one fastq found in {path}. Exiting.')
                sys.exit(1)
        return readset
    elif raw_sequencing_batch.sequencing_type == 'illumina':
        readset.readset_illumina = ReadSetIllumina()
        assert readset_info['path_r1'].endswith('fastq.gz')
        assert readset_info['path_r2'].endswith('fastq.gz')
        readset.readset_illumina.path_r1 = readset_info['path_r1']
        readset.readset_illumina.path_r2 = readset_info['path_r2']
        return readset


def get_nanopore_readset_from_batch_and_barcode(batch_and_barcode_info):
    matching_readset = ReadSetNanopore.query.filter_by(barcode=batch_and_barcode_info['barcode'])\
        .join(ReadSet)\
        .join(ReadSetBatch).filter_by(name=batch_and_barcode_info['readset_batch_name']).all()
    if len(matching_readset) == 0:
        return False
    elif len(matching_readset) == 1:
        return matching_readset[0]


def add_artic_covid_result(artic_covid_result_info):
    readset_nanopore = get_nanopore_readset_from_batch_and_barcode(artic_covid_result_info)
    if readset_nanopore is False:
        print(f"Warning - trying to add artic covid results. There is no readset for barcode {artic_covid_result_info['barcode']} from "
              f"read set batch {artic_covid_result_info['readset_batch_name']}.")
        return
        # sys.exit(1)
    artic_covid_result = read_in_artic_covid_result(artic_covid_result_info)
    readset_nanopore.readset.artic_covid_result.append(artic_covid_result)
    # db.session.add(extraction)
    db.session.commit()
    print(f"Adding artic_covid_result {artic_covid_result_info['sample_name']} from {artic_covid_result_info['readset_batch_name']} to database.")





def add_pangolin_result(pangolin_result_info):
    artic_covid_result = get_artic_covid_result(pangolin_result_info)
    if artic_covid_result is False:
        print(f"Warning - trying to add pangolin results. There is no readset for barcode "
              f"{pangolin_result_info['barcode']} from "
              f"read set batch {pangolin_result_info['readset_batch_name']}.")
        return
    pangolin_result = read_in_pangolin_result(pangolin_result_info)
    artic_covid_result.pangolin_results.append(pangolin_result)
    db.session.commit()
    print(f"Adding pangolin_result {pangolin_result_info['taxon']} from {pangolin_result_info['readset_batch_name']} to database.")


def add_readset(readset_info, covid, nanopore_default):
    # this function has three main parts
    # 1. get the raw_sequencing batch
    # 2. get the extraction
    # 3. get teh raw_sequencing
    #    a. if the raw sequencing doesn't already exist, make it and add it to extraction.
    readset_batch = get_readset_batch(readset_info)
    if readset_batch is False:
        print(
            f"Adding readset. No ReadSetBatch match for {readset_info['readset_batch_name']}, need to add that batch "
            f"and re-run. Exiting.")
        sys.exit(1)
    # this get_raw_sequencing_batch is probably superfluous, because the readset_batch should be guaranteed to have
    #  a raw_seuqencing_batch attribute, and can then just be replaced with an assertion that it's true
    #  but will leave it in for now.
    # assert isinstance(readset_batch.raw_sequencing_batch, RawSequencingBatch)
    raw_sequencing_batch = get_raw_sequencing_batch(readset_batch.raw_sequencing_batch.name)
    if raw_sequencing_batch is False:
        print(f"Adding readset. No RawSequencingBatch match for {readset_info['batch']}, need to add that batch and re-run. Exiting.")
        sys.exit(1)
    # get raw sequencing
    raw_sequencing = get_raw_sequencing(readset_info, readset_batch.raw_sequencing_batch, covid)
    # raw_sequencing will only be True if this is a re-basecalled readset
    if raw_sequencing is False:
        # if it's false, means need to add raw sequencing
        raw_sequencing = read_in_raw_sequencing(readset_info, nanopore_default, raw_sequencing_batch.sequencing_type,
                                                raw_sequencing_batch.batch_directory)
        # need to add raw_seq to raw seq batch
        raw_sequencing_batch.raw_sequencings.append(raw_sequencing)
        if covid is True:
            # if the sample is covid, we need to get the tiling pcr record
            tiling_pcr = get_tiling_pcr(readset_info)
            if tiling_pcr is False:
                print(f"Adding readset. There is no TilingPcr record for sample {readset_info['sample_identifier']} PCRed on "
                      f"{readset_info['date_tiling_pcred']} by group {readset_info['group_name']}. You need to add this. "
                      f"Exiting.")
                sys.exit(1)
            # add the raw_seq to the tiling pcr
            tiling_pcr.raw_sequencings.append(raw_sequencing)
            # then add the raw sequencing to the extraction which was used to generate the PCR as well.
            tiling_pcr.extraction.raw_sequencing.append(raw_sequencing)
        elif covid is False:
            # if it's not covid, don't need the tiling pcr part, so just get the extractions
            extraction = get_extraction(readset_info)
            if extraction is False:
                print(f"Adding readset. No Extraction match for {readset_info['sample_identifier']}, extracted on "
                      f"{readset_info['date_extracted']} for extraction id {readset_info['extraction_identifier']} need to add "
                      f"that extract and re-run. Exiting.")
                sys.exit(1)
            # and add the raw_sequencing to the extraction
            extraction.raw_sequencing.append(raw_sequencing)


    # after having either got the raw_sequencing if this is a re-basecalled set, or read in the raw_sequencing if
    #  it isnt, it's time to read in the readset.
    readset = read_in_readset(readset_info, nanopore_default, raw_sequencing_batch, readset_batch, covid)
    # print(dir(readset))
    readset_batch.readsets.append(readset)
    raw_sequencing.readsets.append(readset)
    # add the readset to the filestructure

    db.session.add(raw_sequencing)
    db.session.commit()
    print(f"Added readset {readset_info['sample_identifier']} to the database.")
