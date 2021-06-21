import os
import csv
import sys
import glob
import yaml
import datetime
from app import db
from app.models import Sample, Project, SampleSource, ReadSet, ReadSetIllumina, ReadSetNanopore, RawSequencingBatch,\
    Extraction, RawSequencing, RawSequencingNanopore, RawSequencingIllumina, TilingPcr, Groups, CovidConfirmatoryPcr


def read_in_config(config_inhandle):
    with open(config_inhandle) as fi:
        return yaml.safe_load(fi)


def read_in_as_dict(inhandle):
    # since csv.DictReader returns a generator rather than an iterator, need to do this fancy business to
    # pull in everything from a generator into an honest to goodness iterable.
    info = csv.DictReader(open(inhandle, encoding='utf-8-sig'))
    # info is a list of ordered dicts, so convert each one to
    list_of_lines = []
    for each_dict in info:
        new_info = {x: each_dict[x] for x in each_dict}
        # sometimes excel saves blank lines, so only take lines where the lenght of the set of teh values is > 1
        # it will be 1 where they are all blank i.e. ''
        if len(set(new_info.values())) > 1:
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
                print(f"Project {project_name} from group {sample_source_info['group_name']} "
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
        print(f"There is more than one matching sample_source with the sample_source_identifier "
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
        print(f"There is more than one matching sample with the sample_identifier "
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
        print(f"More than one Extraction match for {readset_info['sample_identifier']}. Shouldn't happen, exiting.")
        sys.exit()


def add_project(project_info):
    # todo - add get group to add project
    group = get_group(project_info)
    if group is False:
        print(f"No group {project_info['group_name']} from institution {project_info['institution']}. You need to add "
              f"this group. Exiting.")
        sys.exit()
    project = Project(project_name=project_info['project_name'], project_details=project_info['project_details'])
    group.projects.append(project)
    db.session.add(project)
    db.session.commit()


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
        print(f"There is already more than one project called {project_name} from {info['group_name']} at "
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
            print(f"Project {project_name} from group {info['group_name']} "
                  f" doesnt exist in the db, you need to add it using the seqbox_cmd.py "
                  f"add_projects function.\nExiting now.")
            sys.exit()
    return projects


def read_in_sample_info(sample_info):
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
    return sample


def read_in_sample_source_info(sample_source_info):
    if sample_source_info['sample_source_identifier'] == '':
        print(f"sample_source_identifier isn't allowed to be null, check the line which gave rise to "
              f"{sample_source_info}. Exiting.")
        sys.exit()
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
    if extraction_info['processing_institution'] != '':
        extraction.processing_institution = extraction_info['processing_institution']
    return extraction


def read_in_group(group_info):
    group = Groups()
    assert group_info['group_name'] != ''
    assert group_info['institution'] != ''
    group.group_name = group_info['group_name']
    group.institution = group_info['institution']
    return group


def read_in_tiling_pcr(tiling_pcr_info):
    tiling_pcr = TilingPcr()
    if tiling_pcr_info['date_pcred'] != '':
        tiling_pcr.date_pcred = datetime.datetime.strptime(tiling_pcr_info['date_pcred'], '%d/%m/%Y')
    if tiling_pcr_info['pcr_identifier'] != '':
        tiling_pcr.pcr_identifier = tiling_pcr_info['pcr_identifier']
    if tiling_pcr_info['protocol'] != '':
        tiling_pcr.protocol = tiling_pcr_info['protocol']
    if tiling_pcr_info['number_of_cycles'] != '':
        tiling_pcr.number_of_cycles = tiling_pcr_info['number_of_cycles']
    return tiling_pcr


def read_in_covid_confirmatory_pcr(covid_confirmatory_pcr_info):
    covid_confirmatory_pcr = CovidConfirmatoryPcr()
    if covid_confirmatory_pcr_info['date_pcred'] != '':
        covid_confirmatory_pcr.date_pcred = datetime.datetime.strptime(covid_confirmatory_pcr_info['date_pcred'], '%d/%m/%Y')
    if covid_confirmatory_pcr_info['pcr_identifier'] != '':
        covid_confirmatory_pcr.pcr_identifier = covid_confirmatory_pcr_info['pcr_identifier']
    if covid_confirmatory_pcr_info['protocol'] != '':
        covid_confirmatory_pcr.protocol = covid_confirmatory_pcr_info['protocol']
    if covid_confirmatory_pcr_info['ct'] == '':
        covid_confirmatory_pcr.ct = None
    else:
        covid_confirmatory_pcr.ct = covid_confirmatory_pcr_info['ct']
    return covid_confirmatory_pcr


def add_sample(sample_info):
    # sample_info is a dict of one line of the input csv (keys from col header)
    # for the projects listed in the csv, check if they already exist for that group
    # if it does, return it, if it doesnt, instantiate a new Project and return it
    # print(sample_info)
    sample_source = get_sample_source(sample_info)
    if sample_source is False:
        print(f"There is no matching sample_source with the sample_source_identifier "
              f"{sample_info['sample_source_identifier']} for group {sample_info['group_name']}, please add using "
              f"python seqbox_cmd.py add_sample_source and then re-run this command. Exiting.")
        sys.exit()
    # instantiate a new Sample
    sample = read_in_sample_info(sample_info)
    sample_source.samples.append(sample)
    print(f"Adding sample {sample_info['sample_identifier']}")
    db.session.add(sample)
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
    print(f'Adding {sample_source_info["sample_source_identifier"]} to project(s) {projects}')


def add_tiling_pcr(tiling_pcr_info):
    extraction = get_extraction(tiling_pcr_info)
    if extraction is False:
        print(f"No Extraction match for {tiling_pcr_info['sample_identifier']}, extracted on "
              f"{tiling_pcr_info['date_extracted']} for extraction id {tiling_pcr_info['extraction_identifier']} "
              f"need to add that extract and re-run. Exiting.")
        sys.exit()
    tiling_pcr = read_in_tiling_pcr(tiling_pcr_info)
    extraction.tiling_pcrs.append(tiling_pcr)
    db.session.add(tiling_pcr)
    db.session.commit()
    print(f"Adding tiling PCR for sample {tiling_pcr_info['sample_identifier']} run on "
          f"{tiling_pcr_info['date_pcred']} PCR id {tiling_pcr_info['pcr_identifier']} to the database.")


def add_covid_confirmatory_pcr(covid_confirmatory_pcr_info):
    extraction = get_extraction(covid_confirmatory_pcr_info)
    if extraction is False:
        print(f"No Extraction match for {covid_confirmatory_pcr_info['sample_identifier']}, extracted on "
              f"{covid_confirmatory_pcr_info['date_extracted']} for extraction id "
              f"{covid_confirmatory_pcr_info['extraction_identifier']} "
              f"need to add that extract and re-run. Exiting.")
        sys.exit()
    covid_confirmatory_pcr = read_in_covid_confirmatory_pcr(covid_confirmatory_pcr_info)
    extraction.covid_confirmatory_pcrs.append(covid_confirmatory_pcr)
    db.session.add(covid_confirmatory_pcr)
    db.session.commit()
    print(f"Adding confirmatory PCR for sample {covid_confirmatory_pcr_info['sample_identifier']} run on "
          f"{covid_confirmatory_pcr_info['date_pcred']} PCR id {covid_confirmatory_pcr_info['pcr_identifier']} to the database.")


def add_group(group_info):
    group = read_in_group(group_info)
    db.session.add(group)
    db.session.commit()
    print(f"Adding group {group_info['group_name']} from {group_info['institution']} to database.")


def add_extraction(extraction_info):
    sample = get_sample(extraction_info)
    if sample is False:
        print(f"There is no matching sample with the sample_source_identifier "
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
            pcr_identifier=tiling_pcr_info['pcr_identifier'],
            date_pcred=datetime.datetime.strptime(tiling_pcr_info['date_pcred'], '%d/%m/%Y'))\
        .join(Extraction).join(Sample).filter_by(sample_identifier=tiling_pcr_info['sample_identifier']).all()
    if len(matching_tiling_pcr) == 1:
        return matching_tiling_pcr[0]
    elif len(matching_tiling_pcr) == 0:
        return False
    else:
        print(f"More than one match for {tiling_pcr_info['sample_identifier']} on date {tiling_pcr_info['date_run']} "
              f"with pcr_identifier {tiling_pcr_info['pcr_identifier']}. Shouldn't happen, exiting.")
        sys.exit()


def get_covid_confirmatory_pcr(covid_confirmatory_pcr_info):
    matching_covid_confirmatory_pcr = CovidConfirmatoryPcr.query.filter_by(
        pcr_identifier=covid_confirmatory_pcr_info['pcr_identifier'],
        date_pcred=datetime.datetime.strptime(covid_confirmatory_pcr_info['date_pcred'], '%d/%m/%Y'))\
        .join(Extraction).join(Sample).filter_by(sample_identifier=covid_confirmatory_pcr_info['sample_identifier'])\
        .all()
    if len(matching_covid_confirmatory_pcr) == 0:
        return False
    elif len(matching_covid_confirmatory_pcr) == 1:
        return matching_covid_confirmatory_pcr[0]
    else:
        print(f"More than one match for {covid_confirmatory_pcr_info['sample_identifier']} on date"
              f" {covid_confirmatory_pcr_info['date_run']} with pcr_identifier "
              f"{covid_confirmatory_pcr_info['pcr_identifier']}. Shouldn't happen, exiting.")
        sys.exit()


def get_group(group_info):
    matching_group = Groups.query.filter_by(group_name=group_info['group_name'], institution=group_info['institution'])\
        .all()
    if len(matching_group) == 0:
        return False
    elif len(matching_group) == 1:
        return matching_group[0]
    else:
        print(f"More than one match for {group_info['group_name']} from {group_info['institution']}. Shouldn't happen, "
              f"exiting.")
        sys.exit()


def get_readset(readset_info):
    raw_sequencing_batch = get_raw_sequencing_batch(readset_info['batch'])
    if raw_sequencing_batch is False:
        print(f"No RawSequencingBatch match for {readset_info['batch']}, need to add that batch and re-run. "
              f"Exiting.")
        sys.exit()
    read_set_type = None
    if raw_sequencing_batch.sequencing_type == 'illumina':
        read_set_type = ReadSetIllumina
    elif raw_sequencing_batch.sequencing_type == 'nanopore':
        read_set_type = ReadSetNanopore
    # todo - is this going to be a slow query when read_set_ill/nano get big?
    matching_readset = read_set_type.query.join(ReadSet).\
        join(RawSequencing).join(RawSequencingBatch).filter_by(name=readset_info['batch']).join(Extraction)\
        .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier']).join(SampleSource)\
        .join(SampleSource.projects).join(Groups)\
        .filter_by(group_name=readset_info['group_name'])\
        .distinct().all()

    # print(matching_readset)
    if len(matching_readset) == 0:
        return False
    elif len(matching_readset) == 1:
        # todo - the error/info printing needs to be moved out of this function.
        if raw_sequencing_batch.sequencing_type == 'nanopore':
            print(f"This readset ({readset_info['path_fastq']}) already exists in the database for the group "
                  f"{readset_info['group_name']}. Not adding it to the database.")
        elif raw_sequencing_batch.sequencing_type == 'illumina':
            print(f"This readset ({readset_info['path_r1']}) already exists in the database for the group "
                  f"{readset_info['group_name']}. Not adding it to the database.")
        return matching_readset[0]


def read_in_raw_sequencing_batch_info(raw_sequencing_batch_info):
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


def add_raw_sequencing_batch(raw_sequencing_batch_info):
    raw_sequencing_batch = read_in_raw_sequencing_batch_info(raw_sequencing_batch_info)
    db.session.add(raw_sequencing_batch)
    db.session.commit()
    print(f"Added batch {raw_sequencing_batch_info['batch_name']} to the database.")


def get_raw_sequencing_batch(batch_name):
    matching_raw_seq_batch = RawSequencingBatch.query.filter_by(name=batch_name).all()
    if len(matching_raw_seq_batch) == 1:
        return matching_raw_seq_batch[0]
    elif len(matching_raw_seq_batch) == 0:
        return False
    else:
        print(f"More than one match for {batch_name}. Shouldn't happen, exiting.")
        sys.exit()


def get_raw_sequencing(readset_info, raw_sequencing_batch):
    raw_sequencing_type = None
    if raw_sequencing_batch.sequencing_type == 'nanopore':
        raw_sequencing_type = RawSequencingNanopore
    elif raw_sequencing_batch.sequencing_type == 'illumina':
        raw_sequencing_type = RawSequencingIllumina

    matching_raw_sequencing = raw_sequencing_type.query \
        .join(RawSequencing).join(RawSequencingBatch).filter_by(name=readset_info['batch']).join(Extraction) \
        .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier']).join(SampleSource) \
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
        print("this shouldnt happen blkjha")


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
            fast5s = glob.glob(path)
            if len(fast5s) == 1:
                raw_sequencing.raw_sequencing_nanopore.path_fast5 = fast5s[0]
            elif len(fast5s) == 0:
                print(f'No fast5 found in {path}. Exiting.')
                sys.exit()
            elif len(fast5s) > 1:
                print(f'More than one fast5 found in {path}. Exiting.')
                sys.exit()
        elif nanopore_default is False:
            raw_sequencing.raw_sequencing_nanopore.path_fast5 = readset_info['path_fast5']
        # raw_sequencing.raw_sequencing_nanopore.append(raw_sequencing_nanopore)
    return raw_sequencing


def read_in_readset(readset_info, nanopore_default, raw_sequencing_batch):
    readset = ReadSet()
    if raw_sequencing_batch.sequencing_type == 'nanopore':
        readset.read_set_nanopore = ReadSetNanopore()
        if nanopore_default is False:
            # todo - also need to change the fast5 path done as part of read_in_raw_sequencing
            assert readset_info['path_fastq'].endswith('fastq.gz')
            readset.read_set_nanopore.path_fastq = readset_info['path_fastq']
            readset.read_set_filename = readset_info['readset_filename']
        elif nanopore_default is True:
            path = os.path.join(raw_sequencing_batch.batch_directory, 'fastq_pass', readset_info['barcode'], '*fastq.gz')
            fastqs = glob.glob(path)
            # todo - this way of setting read_set_filename is shitty and fragile
            readset.read_set_filename = os.path.basename(fastqs[0]).split('.')[0]
            if len(fastqs) == 1:
                readset.read_set_nanopore.path_fastq = fastqs[0]
            elif len(fastqs) == 0:
                print(f'No fastq found in {path}. Exiting.')
                sys.exit()
            elif len(fastqs) > 1:
                print(f'More than one fastq found in {path}. Exiting.')
                sys.exit()
        readset.read_set_nanopore.basecaller = readset_info['basecaller']
        # readset.nanopore_read_sets.append(read_set_nanopore)
    elif raw_sequencing_batch.sequencing_type == 'illumina':
        readset.read_set_illumina = ReadSetIllumina()
        assert readset_info['path_r1'].endswith('fastq.gz')
        assert readset_info['path_r2'].endswith('fastq.gz')
        readset.read_set_illumina.path_r1 = readset_info['path_r1']
        readset.read_set_illumina.path_r2 = readset_info['path_r2']
    return readset


def add_readset(readset_info, covid, config, nanopore_default):
    # this function has three main parts
    # 1. get the raw_sequencing batch
    # 2. get the extraction
    # 3. get teh raw_sequencing
    #    a. if the raw sequencing doesn't already exist, make it and add it to extraction.
    # todo = need to handle the nanopore_default in this function, which means making full paths for the fastq in the
    #  readset and the fast5 in the raw sequencing, if nanopore_default is True. Use the batch_dir in the
    #  raw_sequencing_batch
    # get the information on the DNA extraction which was sequenced, from the CSV file, return an instance of the
    # Extraction class
    raw_sequencing_batch = get_raw_sequencing_batch(readset_info['batch'])
    if raw_sequencing_batch is False:
        print(f"No RawSequencing match for {readset_info['batch']}, need to add that batch and re-run. Exiting.")
        sys.exit()
    # get raw sequencing
    raw_sequencing = get_raw_sequencing(readset_info, raw_sequencing_batch)
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
                print(f"There is no TilingPcr record for sample {readset_info['sample_identifier']} PCRed on "
                      f"{readset_info['date_pcred']} by group {readset_info['group_name']}. You need to add this. "
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
                print(f"No Extraction match for {readset_info['sample_identifier']}, extracted on "
                      f"{readset_info['date_extracted']} for extraction id {readset_info['extraction_identifier']} need to add "
                      f"that extract and re-run. Exiting.")
                sys.exit()
            # and add the raw_sequencing to the extraction
            extraction.raw_sequencing.append(raw_sequencing)

    readset = read_in_readset(readset_info, nanopore_default, raw_sequencing_batch)
    raw_sequencing.read_sets.append(readset)

    add_readset_to_filestructure(readset, config)
    db.session.add(raw_sequencing)
    db.session.commit()
    print(f"Added read set {readset_info['sample_identifier']} to the database.")
    # todo - need to set read_set_name in the db, after this readset has been added to the db.


def add_readset_to_filestructure(readset, config):
    '''
    1. Check that input files exist
    2. get seqbox_id-filename for this sample
    3. check that output dir exists (make it if not)
        a. will be /Users/flashton/Dropbox/non-project/test_seqbox_data/Core/[seqbox_id]-filename/
    4. link the fastq to the output_dir
    '''
    if readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'nanopore':
        assert os.path.isfile(readset.read_set_nanopore.path_fastq)
        #  todo - what doing with fast5?
        # assert os.path.isfile(readset_info['path_fast5'])
    elif readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'illumina':
        assert os.path.isfile(readset.read_set_illumina.path_r1)
        assert os.path.isfile(readset.read_set_illumina.path_r2)
    projects = readset.raw_sequencing.extraction.sample.sample_source.projects
    group_names = [x.groups.group_name for x in projects]
    # a sample can only belong to one project, so this assertion should always be true.
    assert len(set(group_names)) == 1
    group_name = group_names[0]
    group_dir = os.path.join(config['seqbox_directory'], group_name)
    if not os.path.isdir(group_dir):
        os.mkdir(group_dir)
    sample_name = readset.raw_sequencing.extraction.sample.sample_identifier
    readset_dir = os.path.join(group_dir, f"{readset.seqbox_id}-{sample_name}")
    if not os.path.isdir(readset_dir):
        os.mkdir(readset_dir)
    if readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'nanopore':
        output_readset_fastq_path = os.path.join(readset_dir, f"{readset.seqbox_id}-{sample_name}.fastq.gz")
        if not os.path.isfile(output_readset_fastq_path):
            os.symlink(readset.read_set_nanopore.path_fastq, output_readset_fastq_path)
    elif readset.readset.raw_sequencing.raw_sequencing_batch.sequencing_type == 'illumina':
        output_readset_r1_fastq_path = os.path.join(readset_dir, f"{readset.readset.seqbox_id}-{sample_name}_R1.fastq.gz")
        output_readset_r2_fastq_path = os.path.join(readset_dir, f"{readset.readset.seqbox_id}-{sample_name}_R2.fastq.gz")
        os.symlink(readset.read_set_illumina.path_r1, output_readset_r1_fastq_path)
        os.symlink(readset.read_set_illumina.path_r2, output_readset_r2_fastq_path)
    # if not os.path.isdir(f"{config['seqbox_directory']}/{readset.readset.seqbox_id}-{readset.readset.read_set_filename}")




