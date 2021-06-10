import csv
import sys
import datetime
from app import db
from app.models import Sample, Project, SampleSource, ReadSet, ReadSetIllumina, ReadSetNanopore, RawSequencingBatch,\
    Extraction, RawSequencing, RawSequencingNanopore, RawSequencingIllumina, TilingPcr


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


def check_sample_source_associated_with_project(sample_source, sample_source_info):
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


def does_sample_source_already_exist(sample_source_info):
    # this function checks is a sample source with the specified identifier already exists for this group
    # sample_source is joined to projects by automagic (via sample_source_project)
    # SampleSource.query.with_entities(SampleSource.sample_source_identifier).join(SampleSource.projects)\
    all_sample_sources_for_this_group = \
        SampleSource.query.join(SampleSource.projects)\
        .filter_by(group_name=sample_source_info['group_name']) \
        .distinct()
    # can't help but feel this block could be replaced by sql, but dont know the sql/sqlalchemy for it.
    # make a dictionary of {sample_source_identifier : sample_source db record}
    all_sample_sources_for_this_group = {x.sample_source_identifier: x for x in all_sample_sources_for_this_group}
    # if our sample_source is in the db for this group already
    if sample_source_info['sample_source_identifier'] in all_sample_sources_for_this_group:
        # we need to check if the project we're entering it with here is associated with it in the database
        check_sample_source_associated_with_project(all_sample_sources_for_this_group[sample_source_info['sample_source_identifier']], sample_source_info)
        print(f"This sample source ({sample_source_info['sample_source_identifier']}) already exists in the database "
              f"for the group {sample_source_info['group_name']}")
        return True
    else:
        return False


def get_sample(readset_info):
    matching_sample = Sample.query. \
        filter_by(sample_identifier=readset_info['sample_identifier']) \
        .join(SampleSource) \
        .join(SampleSource.projects) \
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
    # todo - do i need to add a projec/group name to this? what if two projects extract something with the same
    #  identifier on the same day?
    matching_extraction = Extraction.query.filter_by(extraction_identifier=readset_info['extraction_identifier'],
                                                     date_extracted=datetime.datetime.strptime(
                                                         readset_info['date_extracted'], '%d/%m/%Y')) \
        .join(Sample).filter_by(sample_identifier=readset_info['sample_identifier']).all()
    if len(matching_extraction) == 1:
        return matching_extraction[0]
    elif len(matching_extraction) == 0:
        return False
    else:
        print(f"More than one Extraction match for {readset_info['sample_identifier']}. Shouldn't happen, exiting.")
        sys.exit()


def add_project(project_info):
    project = Project(project_name=project_info['project_name'], group_name=project_info['group_name'],
                      institution=project_info['institution'], project_details=project_info['project_details'])
    db.session.add(project)
    db.session.commit()


def query_projects(info, project_name):
    # query_projects differs from does_project_already_exist because query_projects returns an error if it can't
    # find match, while does_project_already_exist returns false
    # combine with does_project_already_exist
    matching_projects = Project.query.filter_by(project_name=project_name,
                                                group_name=info['group_name']).all()
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


def get_sample_source(sample_info):
    # want to find whether this sample_source is already part of this project
    matching_sample_source = SampleSource.query.\
        filter_by(sample_source_identifier=sample_info['sample_source_identifier'])\
        .join(SampleSource.projects)\
        .filter_by(group_name=sample_info['group_name']).all()
    if len(matching_sample_source) == 0:
        print(f"There is no matching sample_source with the sample_source_identifier "
              f"{sample_info['sample_source_identifier']} for group {sample_info['group_name']}, please add using "
              f"python seqbox_cmd.py add_sample_source and then re-run this command. Exiting.")
        sys.exit()
    elif len(matching_sample_source) == 1:
        return matching_sample_source[0]
    else:
        print(f"There is more than one matching sample_source with the sample_source_identifier "
              f"{sample_info['sample_source_identifier']} for group {sample_info['group_name']}, This shouldn't happen. Exiting.")
    # for x in matching_sample_source:
    #     print(x.sample_source_identifier, [y.group_name for y in x.projects])


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
    # todo - sample_source_identifier shouldnt be allowed to be null
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


def add_sample(sample_info):
    # sample_info is a dict of one line of the input csv (keys from col header)
    # for the projects listed in the csv, check if they already exist for that group
    # if it does, return it, if it doesnt, instantiate a new Project and return it
    # print(sample_info)
    sample_source = get_sample_source(sample_info)
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
    print(f'adding {sample_source_info["sample_source_identifier"]} to project(s) {projects}')


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
    print(f"Adding {extraction_info['sample_identifier']} extraction on {extraction_info['date_extracted']} to the DB")
    db.session.commit()


def get_readset(readset_info):
    # todo - is there a nicer way to code this?
    # todo - check readset_info['sequencing_type'] is allowed type
    # todo - isn't the path_fastq or path_r1 enough to distinguish it? doesn't need to belong to that group
    if readset_info['sequencing_type'] == 'nanopore':
        matching_readset = ReadSetNanopore.query.filter_by(path_fastq=readset_info['path_fastq']).join(ReadSet).\
            join(RawSequencing).join(Extraction).join(Sample).join(SampleSource).join(SampleSource.projects).\
            filter_by(group_name=readset_info['group_name'])\
            .distinct().all()
    elif readset_info['sequencing_type'] == 'illumina':
        matching_readset = ReadSetIllumina.query.filter_by(path_r1=readset_info['path_r1']).join(ReadSet).\
            join(RawSequencing).join(Extraction).join(Sample).join(SampleSource).join(SampleSource.projects). \
            filter_by(group_name=readset_info['group_name']) \
            .distinct().all()
    # print(matching_readset)
    if len(matching_readset) == 0:
        return False
    elif len(matching_readset) == 1:
        if readset_info['sequencing_type'] == 'nanopore':
            print(f"This readset ({readset_info['path_fastq']}) already exists in the database for the group "
                  f"{readset_info['group_name']}. Not adding it to the database.")
        elif readset_info['sequencing_type'] == 'illumina':
            print(f"This readset ({readset_info['path_r1']}) already exists in the database for the group "
                  f"{readset_info['group_name']}. Not adding it to the database.")
        return True





def find_matching_raw_sequencing(readset_info):
    # todo - check that readset_info['sequencing_type'] is an allowed value
    if readset_info['sequencing_type'] == 'nanopore':
        matching_raw_sequencing = RawSequencingNanopore.query.filter_by(path_fast5=readset_info['path_fast5']).all()
        return matching_raw_sequencing
    elif readset_info['sequencing_type'] == 'illumina':
        matching_raw_sequencing = RawSequencingIllumina.query.filter_by(path_r1=readset_info['path_r1']).all()
        return matching_raw_sequencing

    print('Only "nanopore" and "illumina" are currently supported sequencing_type values, please check and re-run. '
          'Exiting.')
    sys.exit()


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


def interpret_covid_readset_query(matching_covid_readset, covid_sequencing_info):
    print(matching_covid_readset)
    if len(matching_covid_readset) == 0:
        return False
    elif len(matching_covid_readset) == 1:
        if covid_sequencing_info['sequencing_type'] == 'nanopore':
            print(f"This readset ({covid_sequencing_info['path_fastq']}) already exists in the database for the group "
                  f"{covid_sequencing_info['group_name']}. Not adding it to the database.")
        elif covid_sequencing_info['sequencing_type'] == 'illumina':
            print(f"This readset ({covid_sequencing_info['path_r1']}) already exists in the database for the group "
                  f"{covid_sequencing_info['group_name']}. Not adding it to the database.")
        return True
    else:
        print('this shouldnt happen')


def get_covid_readset(covid_sequencing_info):
    # todo - check that sequencing type is permissible.
    if covid_sequencing_info['sequencing_type'] == 'nanopore':
        matching_covid_readset = ReadSetNanopore.query.filter_by(path_fastq=covid_sequencing_info['path_fastq'])\
            .join(ReadSet).join(RawSequencing).join(TilingPcr).join(Extraction).join(Sample).join(SampleSource)\
            .join(SampleSource.projects)\
            .filter_by(group_name=covid_sequencing_info['group_name'])\
            .distinct().all()
        result = interpret_covid_readset_query(matching_covid_readset, covid_sequencing_info)
        return result
    elif covid_sequencing_info['sequencing_type'] == 'illumina':
        matching_covid_readset = ReadSetIllumina.query.filter_by(path_r1=covid_sequencing_info['path_r1'])\
            .join(ReadSet).join(RawSequencing).join(TilingPcr).join(Extraction).join(Sample).join(SampleSource)\
            .join(SampleSource.projects) \
            .filter_by(group_name=covid_sequencing_info['group_name']) \
            .distinct().all()
        result = interpret_covid_readset_query(matching_covid_readset, covid_sequencing_info)
        return result
    print('this shouldnt run')


def read_in_raw_sequencing_batch_info(raw_sequencing_batch_info):
    raw_sequencing_batch = RawSequencingBatch()
    raw_sequencing_batch.name = raw_sequencing_batch_info['batch_name']
    raw_sequencing_batch.date_run = datetime.datetime.strptime(raw_sequencing_batch_info['date_run'], '%d/%m/%Y')
    raw_sequencing_batch.instrument_model = raw_sequencing_batch_info['instrument_model']
    raw_sequencing_batch.instrument_name = raw_sequencing_batch_info['instrument_name']
    raw_sequencing_batch.library_prep_method = raw_sequencing_batch_info['library_prep_method']
    raw_sequencing_batch.sequencing_centre = raw_sequencing_batch_info['sequencing_centre']
    raw_sequencing_batch.flowcell_type = raw_sequencing_batch_info['flowcell_type']
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


def get_raw_sequencing(readset_info, extraction):
    # this function takes the readset_info and an extraction instance and returns a raw_sequencing instance with a
    # raw_sequencing_ill/nano instance associated with it. if the extraction has been sequenced before then
    # it adds this raw sequencing record to the extraction record.
    matching_raw_tech_sequencing = find_matching_raw_sequencing(readset_info)
    if len(matching_raw_tech_sequencing) == 0:
        # no matching raw sequencing will be the case for 99.999% of illumina (all illumina?) and most nanopore
        raw_sequencing_batch = get_raw_sequencing_batch(readset_info['batch'])
        if raw_sequencing_batch is False:
            print(f"No RawSequencingBatch match for {readset_info['batch']}, need to add that batch and re-run. Exiting.")
            sys.exit()
        raw_sequencing = read_in_raw_sequencing(readset_info)
        extraction.raw_sequencing.append(raw_sequencing)
        return raw_sequencing, extraction
    elif len(matching_raw_tech_sequencing) == 1:
        # if there is already a raw_sequencing record (i.e. this is another basecalling run of the same raw_sequencing
        # data), then extraction is already assocaited with the raw sequencing, so don't need to add.
        return matching_raw_tech_sequencing[0].raw_sequencing, extraction
    else:
        print("this shouldnt happen blkjha")


def read_in_raw_sequencing(readset_info):
    raw_sequencing = RawSequencing()

    # todo - readset_info['sequencing_type'] shouldnt be able to be empty
    # todo - should throw error if sequencing_type isn't in allowed types
    if readset_info['sequencing_type'] != '':
        raw_sequencing.sequencing_type = readset_info['sequencing_type']
    if readset_info['sequencing_type'] == 'illumina':
        raw_sequencing.raw_sequencing_illumina = RawSequencingIllumina()
        raw_sequencing.raw_sequencing_illumina.path_r1 = readset_info['path_r1']
        raw_sequencing.raw_sequencing_illumina.path_r1 = readset_info['path_r2']
    if readset_info['sequencing_type'] == 'nanopore':
        raw_sequencing.raw_sequencing_nanopore = RawSequencingNanopore()
        raw_sequencing.raw_sequencing_nanopore.path_fast5 = readset_info['path_fast5']
        # raw_sequencing.raw_sequencing_nanopore.append(raw_sequencing_nanopore)

    return raw_sequencing


def read_in_readset(readset_info):
    readset = ReadSet()
    readset.read_set_filename = readset_info['readset_filename']
    if readset_info['sequencing_type'] == 'nanopore':
        readset.read_set_nanopore = ReadSetNanopore()
        readset.read_set_nanopore.path_fastq = readset_info['path_fastq']
        readset.read_set_nanopore.basecaller = readset_info['basecaller']
        # readset.nanopore_read_sets.append(read_set_nanopore)
    elif readset_info['sequencing_type'] == 'illumina':
        readset.read_set_illumina = ReadSetIllumina()
        readset.read_set_illumina.path_r1 = readset_info['path_r1']
        readset.read_set_illumina.path_r2 = readset_info['path_r2']
    return readset


def add_readset(readset_info, covid):
    # get the information on the DNA extraction which was sequenced, from the CSV file, return an instance of the
    # Extraction class
    extraction = get_extraction(readset_info)
    if extraction is False:
        print(f"No Extraction match for {readset_info['sample_identifier']}, extracted on "
              f"{readset_info['date_extracted']} for extraction id {readset_info['extraction_identifier']} need to add "
              f"that extract and re-run. Exiting.")
        sys.exit()
    # need to pass extraction in here because need to link raw_sequencing to extract if this is the first time
    # raw sequencing is being added. if it's not the first time the raw_sequencing is being added, the extraction
    # already has raw_seq associated with it.
    # note - using the fast5 and r1 path to identify the raw sequencing dataset.
    # todo - does extraction need to be returned to here? or will it be updated even if not returned.
    raw_sequencing, extraction = get_raw_sequencing(readset_info, extraction)
    raw_sequencing_batch = get_raw_sequencing_batch(readset_info['batch'])
    print("blah bs")
    if raw_sequencing_batch is False:
        print(f"No RawSequencing match for {readset_info['batch']}, need to add that batch and re-run. Exiting.")
        sys.exit()
    raw_sequencing_batch.raw_sequencings.append(raw_sequencing)
    readset = read_in_readset(readset_info)
    raw_sequencing.read_sets.append(readset)

    if covid is True:
        tiling_pcr = get_tiling_pcr(readset_info)

        if tiling_pcr is False:
            print(f"There is no TilingPcr record for sample {readset_info['sample_identifier']} PCRed on "
                  f"{readset_info['date_pcred']} by group {readset_info['group_name']}. You need to add this. Exiting.")
            sys.exit()

        extraction.tiling_pcrs.append(tiling_pcr)
        tiling_pcr.raw_sequencings.append(raw_sequencing)

    db.session.add(raw_sequencing)
    db.session.commit()

    # todo - need to set read_set_name in the db, after this readset has been added to the db.
    # todo - need to handle sequencing_batch
    # todo = need a flag in the input CSV, is this tiling PCR protocol True/False if it's true, then
