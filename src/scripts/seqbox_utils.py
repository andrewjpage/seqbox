import os
import csv
import sys
import glob
import datetime
from app import db
from app.models import Sample, Project, SampleSource, ReadSet, ReadSetIllumina, ReadSetNanopore, RawSequencingBatch,\
    Extraction, RawSequencing, RawSequencingNanopore, RawSequencingIllumina, TilingPcr, Groups, CovidConfirmatoryPcr, \
    ReadSetBatch, PcrResult, PcrAssay, ArticCovidResult, PangolinResult


def read_in_as_dict(inhandle):
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
                sys.exit()
    # and update the database.
    db.session.commit()


def get_sample_source(sample_info):
    # want to find whether this sample_source is already part of this project
    matching_sample_source = SampleSource.query.\
        filter_by(sample_source_identifier=sample_info['sample_source_identifier'])\
        .join(SampleSource.projects)\
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
    matching_sample = Sample.query. \
        filter_by(sample_identifier=readset_info['sample_identifier']) \
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
        sys.exit()


def get_extraction(readset_info):
    matching_extraction = Extraction.query.filter_by(extraction_identifier=readset_info['extraction_identifier'],
                                                     date_extracted=datetime.datetime.strptime(
                                                         readset_info['date_extracted'], '%d/%m/%Y')) \
        .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier'])\
        .join(SampleSource)\
        .join(SampleSource.projects) \
        .join(Groups) \
        .filter_by(group_name=readset_info['group_name'])\
        .all()
    if len(matching_extraction) == 1:
        return matching_extraction[0]
    elif len(matching_extraction) == 0:
        return False
    else:
        print(f"Trying to get extraction. "
              f"More than one Extraction match for {readset_info['sample_identifier']}. Shouldn't happen, exiting.")
        sys.exit()


def add_project(project_info):
    group = get_group(project_info)
    if group is False:
        print(f"Trying to get group to add project. "
              f"No group {project_info['group_name']} from institution {project_info['institution']}. You need to add "
              f"this group. Exiting.")
        sys.exit()
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
        sys.exit()
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
        sys.exit()


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
            sys.exit()
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
        sys.exit()


def get_pangolin_result(pangolin_result_info):
    matching_pangolin_result = PangolinResult.query.join(ArticCovidResult)\
        .filter_by(profile=pangolin_result_info['artic_profile'], workflow=pangolin_result_info['artic_workflow'])\
        .join(ReadSet)\
        .join(ReadSetBatch).filter_by(name=pangolin_result_info['readset_batch_name'])\
        .join(ReadSetNanopore).filter_by(barcode=pangolin_result_info['barcode']).all()
    if len(matching_pangolin_result) == 1:
        return matching_pangolin_result[0]
    elif len(matching_pangolin_result) == 0:
        return False
    else:
        print(f"Trying to get artic_covid_result. "
              f"More than one ArticCovidResult for barcode {pangolin_result_info['barcode']} for "
              f"readset batch {pangolin_result_info['readset_batch_name']}, run with profile {pangolin_result_info['artic_profile']} "
              f"and workflow {pangolin_result_info['artic_workflow']}. Shouldn't happen, exiting.")
        sys.exit()


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


def read_in_extraction(extraction_info):
    extraction = Extraction()
    check_extraction_fields(extraction_info)
    if extraction_info['extraction_identifier'] != '':
        extraction.extraction_identifier = extraction_info['extraction_identifier']
    if extraction_info['extraction_machine'] != '':
        extraction.extraction_machine = extraction_info['extraction_machine']
    if extraction_info['extraction_kit'] != '':
        extraction.extraction_kit = extraction_info['extraction_kit']
    if extraction_info['what_was_extracted'] != '':
        extraction.what_was_extracted = extraction_info['what_was_extracted']
    if extraction_info['date_extracted'] != '':
        extraction.date_extracted = datetime.datetime.strptime(extraction_info['date_extracted'], '%d/%m/%Y')
    if extraction_info['extraction_processing_institution'] != '':
        extraction.processing_institution = extraction_info['extraction_processing_institution']
    if extraction_info['extraction_from'] != '':
        extraction.extraction_from = extraction_info['extraction_from']
    return extraction


def read_in_group(group_info):
    check_group(group_info)
    group = Groups()
    group.group_name = group_info['group_name']
    group.institution = group_info['institution']
    group.pi = group_info['pi']
    return group


def read_in_tiling_pcr(tiling_pcr_info):
    check_tiling_pcr(tiling_pcr_info)
    tiling_pcr = TilingPcr()
    if tiling_pcr_info['date_tiling_pcred'] != '':
        tiling_pcr.date_pcred = datetime.datetime.strptime(tiling_pcr_info['date_tiling_pcred'], '%d/%m/%Y')
    if tiling_pcr_info['tiling_pcr_identifier'] != '':
        tiling_pcr.pcr_identifier = tiling_pcr_info['tiling_pcr_identifier']
    if tiling_pcr_info['tiling_pcr_protocol'] != '':
        tiling_pcr.protocol = tiling_pcr_info['tiling_pcr_protocol']
    if tiling_pcr_info['number_of_cycles'] != '':
        tiling_pcr.number_of_cycles = tiling_pcr_info['number_of_cycles']
    return tiling_pcr


def check_pangolin_result(pangolin_result_info):
    if pangolin_result_info['taxon'].strip() == '':
        print(f'taxon column should not be empty. it is for \n{pangolin_result_info}\nExiting.')
        sys.exit()
    if pangolin_result_info['lineage'].strip() == '':
        print(f'lineage column should not be empty. it is for \n{pangolin_result_info}\nExiting.')
        sys.exit()
    if pangolin_result_info['status'].strip() == '':
        print(f'status column should not be empty. it is for \n{pangolin_result_info}\nExiting.')
        sys.exit()


def check_artic_covid_result(artic_covid_result_info):
    if artic_covid_result_info['sample_name'].strip() == '':
        print(f'sample_name column should not be empty. it is for \n{artic_covid_result_info}\nExiting.')
        sys.exit()
    if artic_covid_result_info['pct_N_bases'].strip() == '':
        print(f'pct_N_bases column should not be empty. it is for \n{artic_covid_result_info}\nExiting.')
        sys.exit()
    if artic_covid_result_info['pct_covered_bases'].strip() == '':
        print(f'pct_covered_bases column should not be empty. it is for \n{artic_covid_result_info}\nExiting.')
        sys.exit()
    if artic_covid_result_info['num_aligned_reads'].strip() == '':
        print(f'num_aligned_reads column should not be empty. it is for \n{artic_covid_result_info}\nExiting.')
        sys.exit()


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
    pangolin_result.pangolearn_version = pangolin_result_info['pangoLEARN_version']
    pangolin_result.pango_version = pangolin_result_info['pango_version']
    pangolin_result.status = pangolin_result_info['status']
    pangolin_result.note = pangolin_result_info['note']
    return pangolin_result


def read_in_covid_confirmatory_pcr(covid_confirmatory_pcr_info):
    check_covid_confirmatory_pcr(covid_confirmatory_pcr_info)
    covid_confirmatory_pcr = CovidConfirmatoryPcr()
    if covid_confirmatory_pcr_info['date_covid_confirmatory_pcred'] != '':
        covid_confirmatory_pcr.date_pcred = datetime.datetime.strptime(covid_confirmatory_pcr_info['date_covid_confirmatory_pcred'], '%d/%m/%Y')
    if covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier'] != '':
        covid_confirmatory_pcr.pcr_identifier = covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier']
    if covid_confirmatory_pcr_info['covid_confirmatory_pcr_protocol'] != '':
        covid_confirmatory_pcr.protocol = covid_confirmatory_pcr_info['covid_confirmatory_pcr_protocol']
    if covid_confirmatory_pcr_info['covid_confirmatory_pcr_ct'] == '':
        covid_confirmatory_pcr.ct = None
    else:
        covid_confirmatory_pcr.ct = covid_confirmatory_pcr_info['ct']
    return covid_confirmatory_pcr


def read_in_pcr_result(pcr_result_info):
    check_pcr_result(pcr_result_info)
    pcr_result = PcrResult()
    if pcr_result_info['date_pcred'] != '':
        pcr_result.date_pcred = datetime.datetime.strptime(pcr_result_info['date_pcred'], '%d/%m/%Y')
    if pcr_result_info['pcr_identifier'] != '':
        pcr_result.pcr_identifier = pcr_result_info['pcr_identifier']
    if pcr_result_info['ct'] == '':
        pcr_result.ct = None
    else:
        pcr_result.ct = pcr_result_info['ct']
    if pcr_result_info['result'] != '':
        pcr_result.pcr_result = pcr_result_info['result']
    return pcr_result


def add_sample(sample_info):
    # sample_info is a dict of one line of the input csv (keys from col header)
    # for the projects listed in the csv, check if they already exist for that group
    # if it does, return it, if it doesnt, instantiate a new Project and return it
    # print(sample_info)
    sample_source = get_sample_source(sample_info)
    if sample_source is False:
        print(f"Adding sample. There is no matching sample_source with the sample_source_identifier "
              f"{sample_info['sample_source_identifier']} for group {sample_info['group_name']}, please add using "
              f"python seqbox_cmd.py add_sample_source and then re-run this command. Exiting.")
        sys.exit()
    # instantiate a new Sample
    sample = read_in_sample_info(sample_info)
    sample_source.samples.append(sample)
    db.session.add(sample)
    db.session.commit()
    print(f"Adding sample {sample_info['sample_identifier']}")


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
        sys.exit()
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
        sys.exit()
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
    check_pcr_result(pcr_result_info)
    pcr_result = read_in_pcr_result(pcr_result_info)
    assay = get_pcr_assay(pcr_result_info)
    assay.pcr_results.append(pcr_result)
    sample = get_sample(pcr_result_info)
    if sample is False:
        print(f"Adding pcr result, cant find sample for this result:\n{pcr_result_info}\nExiting.")
        sys.exit()
    sample.pcr_results.append(pcr_result)
    db.session.add(pcr_result)
    db.session.commit()
    print(f"Adding pcr_result for {pcr_result_info['sample_identifier']}, assay {pcr_result_info['assay_name']} to "
          f"database.")


def add_extraction(extraction_info):
    sample = get_sample(extraction_info)
    if sample is False:
        print(f"Adding extraction. There is no matching sample with the sample_source_identifier "
              f"{extraction_info['sample_identifier']} for group {extraction_info['group_name']}, please add using "
              f"python seqbox_cmd.py add_sample and then re-run this command. Exiting.")
        sys.exit()
    extraction = read_in_extraction(extraction_info)
    sample.extractions.append(extraction)
    db.session.add(extraction)
    db.session.commit()
    print(f"Adding {extraction_info['sample_identifier']} extraction on {extraction_info['date_extracted']} to the DB")


def get_tiling_pcr(tiling_pcr_info):
    matching_tiling_pcr = TilingPcr.query\
        .filter_by(
            pcr_identifier=tiling_pcr_info['tiling_pcr_identifier'],
            date_pcred=datetime.datetime.strptime(tiling_pcr_info['date_tiling_pcred'], '%d/%m/%Y'))\
        .join(Extraction).join(Sample).filter_by(sample_identifier=tiling_pcr_info['sample_identifier']).all()
    if len(matching_tiling_pcr) == 1:
        return matching_tiling_pcr[0]
    elif len(matching_tiling_pcr) == 0:
        return False
    else:
        print(f"Getting tiling PCR. More than one match for {tiling_pcr_info['sample_identifier']} on date "
              f"{tiling_pcr_info['date_tiling_pcred']} "
              f"with pcr_identifier {tiling_pcr_info['tiling_pcr_identifier']}. Shouldn't happen, exiting.")
        sys.exit()


def get_covid_confirmatory_pcr(covid_confirmatory_pcr_info):
    matching_covid_confirmatory_pcr = CovidConfirmatoryPcr.query.filter_by(
        pcr_identifier=covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier'],
        date_pcred=datetime.datetime.strptime(covid_confirmatory_pcr_info['date_covid_confirmatory_pcred'], '%d/%m/%Y'))\
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
        sys.exit()


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
        sys.exit()


def get_pcr_result(pcr_result_info):
    assay = get_pcr_assay(pcr_result_info)
    if assay is False:
        print(f"There is no pcr assay called {pcr_result_info['assay_name']} in the database, please add it and re-run. "
              f"Exiting.")
        sys.exit()
    matching_pcr_result = PcrResult.query.filter_by(date_pcred=pcr_result_info['date_pcred'],
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
        sys.exit()


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
        sys.exit()


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
        sys.exit()


def get_readset(readset_info, covid):
    # first we get the readset batch so that we can get the raw sequencing batch so that we can get the sequencing type
    readset_batch = get_readset_batch(readset_info)
    if readset_batch is False:
        print(
            f"Getting readset. No ReadSetBatch match for {readset_info['readset_batch_name']}, need to add that batch "
            f"and re-run. Exiting.")
        sys.exit()
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
        sys.exit()

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
    if covid is False:
        matching_readset = readset_type.query.join(ReadSet)\
            .join(ReadSetBatch).filter_by(name=readset_info['readset_batch_name'])\
            .join(RawSequencing) \
            .join(Extraction).filter_by(date_extracted=readset_info['date_extracted'],
                                        extraction_identifier=readset_info['extraction_identifier']) \
            .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier'])\
            .join(SampleSource)\
            .join(SampleSource.projects)\
            .join(Groups)\
            .filter_by(group_name=readset_info['group_name'])\
            .distinct().all()
    # if the sample is covid, then need to match against the tiling pcr
    elif covid is True:
        matching_readset = readset_type.query.join(ReadSet)\
            .join(ReadSetBatch).filter_by(name=readset_info['readset_batch_name']) \
            .join(RawSequencing) \
            .join(TilingPcr).filter_by(date_pcred=readset_info['date_tiling_pcred'],
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


def read_in_raw_sequencing_batch_info(raw_sequencing_batch_info):
    check_raw_sequencing_batch(raw_sequencing_batch_info)
    raw_sequencing_batch = RawSequencingBatch()
    raw_sequencing_batch.name = raw_sequencing_batch_info['batch_name']
    raw_sequencing_batch.date_run = datetime.datetime.strptime(raw_sequencing_batch_info['date_run'], '%d/%m/%Y')
    raw_sequencing_batch.instrument_model = raw_sequencing_batch_info['instrument_model']
    raw_sequencing_batch.instrument_name = raw_sequencing_batch_info['instrument_name']
    raw_sequencing_batch.library_prep_method = raw_sequencing_batch_info['library_prep_method']
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
        sys.exit()


def get_raw_sequencing(readset_info, raw_sequencing_batch, covid):
    raw_sequencing_type = None
    if raw_sequencing_batch.sequencing_type == 'nanopore':
        raw_sequencing_type = RawSequencingNanopore
    elif raw_sequencing_batch.sequencing_type == 'illumina':
        raw_sequencing_type = RawSequencingIllumina

    if covid is True:
        matching_raw_sequencing = raw_sequencing_type.query \
            .join(RawSequencing) \
            .join(RawSequencingBatch).filter_by(name=raw_sequencing_batch.name) \
            .join(Extraction)\
            .join(TilingPcr).filter_by(pcr_identifier=readset_info['tiling_pcr_identifier'],
                                        date_pcred=datetime.datetime.strptime(
                                            readset_info['date_tiling_pcred'], '%d/%m/%Y')) \
            .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier']) \
            .join(SampleSource) \
            .join(SampleSource.projects).join(Groups) \
            .filter_by(group_name=readset_info['group_name']) \
            .distinct().all()
    elif covid is False:
        matching_raw_sequencing = raw_sequencing_type.query \
            .join(RawSequencing)\
            .join(RawSequencingBatch).filter_by(name=raw_sequencing_batch.name)\
            .join(Extraction).filter_by(extraction_identifier=readset_info['extraction_identifier'],
                                                         date_extracted=datetime.datetime.strptime(
                                                             readset_info['date_extracted'], '%d/%m/%Y')) \
            .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier'])\
            .join(SampleSource) \
            .join(SampleSource.projects).join(Groups) \
            .filter_by(group_name=readset_info['group_name']) \
            .distinct().all()

    if len(matching_raw_sequencing) == 0:
        # no matching raw sequencing will be the case for 99.999% of illumina (all illumina?) and most nanopore
        return False

    elif len(matching_raw_sequencing) == 1:
        # if there is already a raw_sequencing record (i.e. this is another basecalling run of the same raw_sequencing
        # data), then extraction is already assocaited with the raw sequencing, so don't need to add.
        # we use the matching_raw_tech_sequencing[0].raw_sequencing because the find_matching_raw_sequencing() query
        # returns an Illumina/NanoporeRawSequencing class.
        return matching_raw_sequencing[0].raw_sequencing
    else:
        print(f"Getting raw_sequencing, more than one match in {readset_info['batch']} for sample "
              f"{readset_info['sample_identifier']} from group {readset_info['group_name']}. This shouldn't happen.")


def read_in_raw_sequencing(readset_info, nanopore_default, sequencing_type, batch_directory):
    raw_sequencing = RawSequencing()
    if sequencing_type == 'illumina':
        raw_sequencing.raw_sequencing_illumina = RawSequencingIllumina()
        raw_sequencing.raw_sequencing_illumina.path_r1 = readset_info['path_r1']
        raw_sequencing.raw_sequencing_illumina.path_r1 = readset_info['path_r2']
    if sequencing_type == 'nanopore':
        raw_sequencing.raw_sequencing_nanopore = RawSequencingNanopore()
        if nanopore_default is True:
            path = os.path.join(batch_directory, 'fast5_pass', readset_info['barcode'], '*fast5')
            raw_sequencing.raw_sequencing_nanopore.path_fast5 = path
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
        sys.exit()
    if raw_sequencing_batch_info['batch_name'].strip() == '':
        print(f'batch_name column should not be empty. it is for \n{raw_sequencing_batch_info}\nExiting.')
        sys.exit()
    if raw_sequencing_batch_info['date_run'].strip() == '':
        print(f'date_run column should not be empty. it is for \n{raw_sequencing_batch_info}\nExiting.')
        sys.exit()
    if raw_sequencing_batch_info['sequencing_type'].strip() == '':
        print(f'sequencing_type column should not be empty. it is for \n{raw_sequencing_batch_info}\nExiting.')
        sys.exit()
    if raw_sequencing_batch_info['instrument_name'].strip() == '':
        print(f'batch_directory column should not be empty. it is for \n{raw_sequencing_batch_info}\nExiting.')
        sys.exit()
    if raw_sequencing_batch_info['library_prep_method'].strip() == '':
        print(f'batch_name column should not be empty. it is for \n{raw_sequencing_batch_info}\nExiting.')
        sys.exit()
    if raw_sequencing_batch_info['flowcell_type'].strip() == '':
        print(f'date_run column should not be empty. it is for \n{raw_sequencing_batch_info}\nExiting.')
        sys.exit()


def check_readset_batches(readset_batch_info):
    if readset_batch_info['raw_sequencing_batch_name'].strip() == '':
        print(f'raw_sequencing_batch_name column should not be empty. it is for \n{readset_batch_info}\nExiting.')
        sys.exit()
    if readset_batch_info['readset_batch_name'].strip() == '':
        print(f'readset_batch_name column should not be empty. it is for \n{readset_batch_info}\nExiting.')
        sys.exit()
    if readset_batch_info['readset_batch_dir'].strip() == '':
        print(f'readset_batch_dir column should not be empty. it is for \n{readset_batch_info}\nExiting.')
        sys.exit()
    if readset_batch_info['basecaller'].strip() == '':
        print(f'basecaller column should not be empty. it is for \n{readset_batch_info}\nExiting.')
        sys.exit()


def check_extraction_fields(extraction_info):
    if extraction_info['sample_identifier'].strip() == '':
        print(f'sample_identifier column should not be empty. it is for \n{extraction_info}\nExiting.')
        sys.exit()
    if extraction_info['date_extracted'].strip() == '':
        print(f'date_extracted column should not be empty. it is for \n{extraction_info}\nExiting.')
        sys.exit()
    if extraction_info['extraction_identifier'].strip() == '':
        print(f'extraction_identifier column should not be empty. it is for \n{extraction_info}\nExiting.')
        sys.exit()
    if extraction_info['group_name'].strip() == '':
        print(f'extraction_identifier column should not be empty. it is for \n{extraction_info}\nExiting.')
        sys.exit()
    # if extraction_info['extraction_from'].strip() == '':
    #     print(f'extraction_from column should not be empty. it is for \n{extraction_info}\nExiting.')
    #     sys.exit()


def check_group(group_info):
    if ' ' in group_info['group_name']:
        print(f'group_name should not have any spaces in in. there is one for \n{group_info}\nExiting.')
        sys.exit()
    if '/' in group_info['group_name']:
        print(f'group_name should not have any backslashes in in. there is one for \n{group_info}\nExiting.')
        sys.exit()
    if group_info['group_name'].strip() == '':
        print(f'group_name column should not be empty. it is for \n{group_info}\nExiting.')
        sys.exit()
    if group_info['institution'].strip() == '':
        print(f'institution column should not be empty. it is for \n{group_info}\nExiting.')
        sys.exit()


def check_project(project_info):
    if project_info['project_name'].strip() == '':
        print(f'project_name column should not be empty. it is for \n{project_info}\nExiting.')
        sys.exit()
    if project_info['group_name'].strip() == '':
        print(f'group_name column should not be empty. it is for \n{project_info}\nExiting.')
        sys.exit()
    if project_info['institution'].strip() == '':
        print(f'institution column should not be empty. it is for \n{project_info}\nExiting.')
        sys.exit()


def check_sample_sources(sample_source_info):
    if sample_source_info['sample_source_identifier'].strip() == '':
        print(f'sample_source_identifier column should not be empty. it is for \n{sample_source_info}\nExiting.')
        sys.exit()
    if sample_source_info['sample_source_type'].strip() == '':
        print(f'sample_source_type column should not be empty. it is for \n{sample_source_info}\nExiting.')
        sys.exit()
    if sample_source_info['projects'].strip() == '':
        print(f'projects column should not be empty. it is for \n{sample_source_info}\nExiting.')
        sys.exit()
    if sample_source_info['group_name'].strip() == '':
        print(f'group_name column should not be empty. it is for \n{sample_source_info}\nExiting.')
        sys.exit()
    if sample_source_info['institution'].strip() == '':
        print(f'institution column should not be empty. it is for \n{sample_source_info}\nExiting.')
        sys.exit()


def check_samples(sample_info):
    if sample_info['sample_source_identifier'].strip() == '':
        print(f'sample_source_identifier column should not be empty. it is for \n{sample_info}\nExiting.')
        sys.exit()
    if sample_info['sample_identifier'].strip() == '':
        print(f'sample_identifier column should not be empty. it is for \n{sample_info}\nExiting.')
        sys.exit()
    if sample_info['group_name'].strip() == '':
        print(f'group_name column should not be empty. it is for \n{sample_info}\nExiting.')
        sys.exit()
    if sample_info['institution'].strip() == '':
        print(f'institution column should not be empty. it is for \n{sample_info}\nExiting.')
        sys.exit()


def check_covid_confirmatory_pcr(covid_confirmatory_pcr_info):
    if covid_confirmatory_pcr_info['sample_identifier'].strip() == '':
        print(f'sample_identifier column should not be empty. it is for \n{covid_confirmatory_pcr_info}\nExiting.')
        sys.exit()
    if covid_confirmatory_pcr_info['date_extracted'].strip() == '':
        print(f'date_extracted column should not be empty. it is for \n{covid_confirmatory_pcr_info}\nExiting.')
        sys.exit()
    if covid_confirmatory_pcr_info['extraction_identifier'].strip() == '':
        print(f'extraction_identifier column should not be empty. it is for \n{covid_confirmatory_pcr_info}\nExiting.')
        sys.exit()
    if covid_confirmatory_pcr_info['date_covid_confirmatory_pcred'].strip() == '':
        print(f'date_covid_confirmatory_pcred column should not be empty. it is for '
              f'\n{covid_confirmatory_pcr_info}\nExiting.')
        sys.exit()
    if covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier'].strip() == '':
        print(f'covid_confirmatory_pcr_identifier column should not be empty. it is for '
              f'\n{covid_confirmatory_pcr_info}\nExiting.')
        sys.exit()
    if covid_confirmatory_pcr_info['group_name'].strip() == '':
        print(f'group_name column should not be empty. it is for \n{covid_confirmatory_pcr_info}\nExiting.')
        sys.exit()
    if covid_confirmatory_pcr_info['covid_confirmatory_pcr_protocol'].strip() == '':
        print(f'covid_confirmatory_pcr_protocol column should not be empty. it is for \n{covid_confirmatory_pcr_info}\nExiting.')
        sys.exit()


def check_tiling_pcr(tiling_pcr_info):
    if tiling_pcr_info['sample_identifier'].strip() == '':
        print(f'sample_identifier column should not be empty. it is for \n{tiling_pcr_info}\nExiting.')
        sys.exit()
    if tiling_pcr_info['date_extracted'].strip() == '':
        print(f'date_extracted column should not be empty. it is for \n{tiling_pcr_info}\nExiting.')
        sys.exit()
    if tiling_pcr_info['extraction_identifier'].strip() == '':
        print(f'extraction_identifier column should not be empty. it is for \n{tiling_pcr_info}\nExiting.')
        sys.exit()
    if tiling_pcr_info['date_tiling_pcred'].strip() == '':
        print(f'date_tiling_pcred column should not be empty. it is for \n{tiling_pcr_info}\nExiting.')
        sys.exit()
    if tiling_pcr_info['tiling_pcr_identifier'].strip() == '':
        print(f'pcr_identifier column should not be empty. it is for \n{tiling_pcr_info}\nExiting.')
        sys.exit()
    if tiling_pcr_info['group_name'].strip() == '':
        print(f'group_name column should not be empty. it is for \n{tiling_pcr_info}\nExiting.')
        sys.exit()
    if tiling_pcr_info['tiling_pcr_protocol'].strip() == '':
        print(f'tiling_pcr_protocol column should not be empty. it is for \n{tiling_pcr_info}\nExiting.')
        sys.exit()
    # if tiling_pcr_info['number_of_cycles'].strip() == '':
    #     print(f'number_of_cycles column should not be empty. it is for \n{tiling_pcr_info}\nExiting.')
    #     sys.exit()


def check_pcr_result(pcr_result_info):
    to_check = ['sample_identifier', 'date_pcred', 'pcr_identifier', 'group_name', 'assay_name', 'result']
    for r in to_check:
        if pcr_result_info[r].strip() == '':
            print(f'{r} column should not be empty. it is for \n{pcr_result_info}\nExiting.')
            sys.exit()
    allowable_results = {'Negative', 'Negative - Followup', 'Positive - Followup', 'Positive',
                         'Indeterminate'}
    if pcr_result_info['result'] not in allowable_results:
        print(f'result column should contain one of these results {allowable_results}. '
              f'it doesnt for \n{pcr_result_info}\nExiting.')
        sys.exit()
        

def check_readset_fields(readset_info, nanopore_default, raw_sequencing_batch, covid):
    to_check = ['data_storage_device', 'sample_identifier', 'group_name', 'readset_batch_name']
    for r in to_check:
        if readset_info[r].strip() == '':
            print(f'{r} column should not be empty. it is for \n{readset_info}\nExiting.')
            sys.exit()
    if raw_sequencing_batch.sequencing_type == 'nanopore':
        if nanopore_default is True:
            if readset_info['barcode'].strip() == '':
                print(f'barcode column should not be empty. it is for \n{readset_info}\nExiting.')
                sys.exit()
        else:
            if readset_info['path_fastq'].strip() == '':
                print(f'barcode column should not be empty. it is for \n{readset_info}\nExiting.')
                sys.exit()
            if readset_info['path_fast5'].strip() == '':
                print(f'barcode column should not be empty. it is for \n{readset_info}\nExiting.')
                sys.exit()
    elif raw_sequencing_batch.sequencing_type == 'illumina':
        if readset_info['path_r1'].strip() == '':
            print(f'path_r1 column should not be empty. it is for \n{readset_info}\nExiting.')
            sys.exit()
        if readset_info['path_r2'].strip() == '':
            print(f'path_r2 column should not be empty. it is for \n{readset_info}\nExiting.')
            sys.exit()
    if covid is True:
        if readset_info['date_tiling_pcred'].strip() == '':
            print(f'date_tiling_pcred column should not be empty. it is for \n{readset_info}\nExiting.')
            sys.exit()
        if readset_info['tiling_pcr_identifier'].strip() == '':
            print(f'tiling_pcr_identifier column should not be empty. it is for \n{readset_info}\nExiting.')
            sys.exit()
    else:
        if readset_info['date_extracted'].strip() == '':
            print(f'date_extracted column should not be empty. it is for \n{readset_info}\nExiting.')
            sys.exit()
        if readset_info['extraction_identifier'].strip() == '':
            print(f'extraction_identifier column should not be empty. it is for \n{readset_info}\nExiting.')
            sys.exit()


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
                sys.exit()
            elif len(fastqs) > 1:
                print(f'Reading in readset. More than one fastq found in {path}. Exiting.')
                sys.exit()
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
        # sys.exit()
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
    print(f"Adding artic_covid_result {pangolin_result_info['taxon']} from {pangolin_result_info['readset_batch_name']} to database.")


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
        sys.exit()
    # this get_raw_sequencing_batch is probably superfluous, because the readset_batch should be guaranteed to have
    #  a raw_seuqencing_batch attribute, and can then just be replaced with an assertion that it's true
    #  but will leave it in for now.
    # assert isinstance(readset_batch.raw_sequencing_batch, RawSequencingBatch)
    raw_sequencing_batch = get_raw_sequencing_batch(readset_batch.raw_sequencing_batch.name)
    if raw_sequencing_batch is False:
        print(f"Adding readset. No RawSequencingBatch match for {readset_info['batch']}, need to add that batch and re-run. Exiting.")
        sys.exit()
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
                sys.exit()
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
                sys.exit()
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







