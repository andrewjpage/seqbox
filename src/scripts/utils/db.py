import glob
import os
import sys

import sqlalchemy
from sqlalchemy.orm import sessionmaker

from app import db
from app.models import (
    ArticCovidResult,
    CovidConfirmatoryPcr,
    Culture,
    Extraction,
    Groups,
    Mykrobe,
    PangolinResult,
    PcrResult,
    PcrAssay,
    Project,
    RawSequencingBatch,
    RawSequencing,
    RawSequencingNanopore,
    RawSequencingIllumina,
    ReadSet,
    ReadSetBatch,
    ReadSetIllumina,
    ReadSetNanopore,
    Sample,
    SampleSource,
    TilingPcr,
)

from scripts.utils.check import (
    check_cultures,
    check_empty_fields,
    check_invalid_characters,
    check_pangolin_result,
    check_pcr_result,
    check_readset_fields,
    check_samples,
    rename_dodgy_mykrobe_variables,
)


def add_artic_covid_result(artic_covid_result_info: dict):
    """
    Add an artic covid result to the database.

    Args:
        artic_covid_result_info (dict): a dictionary containing the artic covid result information
    """
    readset_nanopore = get_nanopore_readset_from_batch_and_barcode(artic_covid_result_info)
    if not readset_nanopore:
        print(f"Warning - trying to add artic covid results. There is no readset for barcode {artic_covid_result_info['barcode']} from "
              f"read set batch {artic_covid_result_info['readset_batch_name']}.")
        return False
        # sys.exit(1)
    artic_covid_result = read_in_artic_covid_result(artic_covid_result_info)
    readset_nanopore.readset.artic_covid_result.append(artic_covid_result)
    # db.session.add(extraction)
    db.session.commit()
    print(f"Adding artic_covid_result {artic_covid_result_info['sample_name']} from {artic_covid_result_info['readset_batch_name']} to database.")


def get_artic_covid_result(artic_covid_result_info: dict) -> ArticCovidResult:
    """
    Get an artic covid result from the database.

    Args:
        artic_covid_result_info (dict): a dictionary containing the artic covid result information

    Returns:
        ArticCovidResult: the artic covid result object, or False if there is no match
    """
    matching_artic_covid_result = ArticCovidResult.query \
        .filter_by(
            profile=artic_covid_result_info['artic_profile'],
            workflow=artic_covid_result_info['artic_workflow']
        ) \
        .join(ReadSet) \
        .join(ReadSetBatch) \
        .filter_by(name=artic_covid_result_info['readset_batch_name']) \
        .join(ReadSetNanopore) \
        .filter_by(barcode=artic_covid_result_info['barcode']).all()
    if len(matching_artic_covid_result) == 1:
        return matching_artic_covid_result[0]
    elif len(matching_artic_covid_result) == 0:
        return False
    else:
        print(
            f"Trying to get artic_covid_result. \n"
            f"More than one ArticCovidResult for barcode {artic_covid_result_info['barcode']} "
            f"for readset batch {artic_covid_result_info['readset_batch_name']}, run with "
            f"profile {artic_covid_result_info['artic_profile']} and workflow "
            f"{artic_covid_result_info['artic_workflow']}. \n"
            f"This should not happen. Exiting."
        )
        sys.exit(1)


def read_in_artic_covid_result(artic_covid_result_info: dict) -> ArticCovidResult:
    """
    Read in an artic covid results into an ArticCovidResult object.

    Args:
        artic_covid_result_info (dict): a dictionary containing the artic covid result information
    
    Returns:
        ArticCovidResult: the artic covid result object
    """
    # Check that artic_covid_result_info required fields are not empty
    check_empty_fields(
        artic_covid_result_info,
        ['sample_name', 'pct_N_bases', 'pct_covered_bases', 'num_aligned_reads']
    )
    artic_covid_result = ArticCovidResult()
    artic_covid_result.sample_name = artic_covid_result_info['sample_name']
    artic_covid_result.pct_N_bases = artic_covid_result_info['pct_N_bases']
    artic_covid_result.pct_covered_bases = artic_covid_result_info['pct_covered_bases']
    artic_covid_result.num_aligned_reads = artic_covid_result_info['num_aligned_reads']
    artic_covid_result.workflow = artic_covid_result_info['artic_workflow']
    artic_covid_result.profile = artic_covid_result_info['artic_profile']
    return artic_covid_result


def add_covid_confirmatory_pcr(covid_confirmatory_pcr_info: dict):
    """
    Add a covid confirmatory pcr result to the database.

    Args:
        covid_confirmatory_pcr_info (dict): a dictionary containing the covid confirmatory pcr
                                            result information
    """
    extraction = get_extraction(covid_confirmatory_pcr_info)
    if not extraction:
        print(
            f"Adding covid confirmatory PCR. "
            f"No Extraction match for {covid_confirmatory_pcr_info['sample_identifier']}, "
            f"extracted on {covid_confirmatory_pcr_info['date_extracted']} for extraction id "
            f"{covid_confirmatory_pcr_info['extraction_identifier']} "
            f"need to add that extract and re-run. Exiting."
        )
        sys.exit(1)
    covid_confirmatory_pcr = read_in_covid_confirmatory_pcr(covid_confirmatory_pcr_info)
    extraction.covid_confirmatory_pcrs.append(covid_confirmatory_pcr)
    db.session.add(covid_confirmatory_pcr)
    db.session.commit()
    print(
        f"Adding confirmatory PCR for sample {covid_confirmatory_pcr_info['sample_identifier']} "
        f"run on {covid_confirmatory_pcr_info['date_covid_confirmatory_pcred']} PCR id "
        f"{covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier']} to the database."
    )


def get_covid_confirmatory_pcr(covid_confirmatory_pcr_info: dict) -> CovidConfirmatoryPcr:
    """
    Get a covid confirmatory pcr result from the database.

    Args:
        covid_confirmatory_pcr_info (dict): a dictionary containing the covid confirmatory pcr
                                            result information

    Returns:
        CovidConfirmatoryPcr: the covid confirmatory pcr object, or False if there is no match
    """
    matching_covid_confirmatory_pcr = CovidConfirmatoryPcr.query.filter_by(
            pcr_identifier=covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier'],
            date_pcred=covid_confirmatory_pcr_info['date_covid_confirmatory_pcred'] ) \
        .join(Extraction) \
        .filter_by(
            extraction_identifier=covid_confirmatory_pcr_info['extraction_identifier'],
            date_extracted=covid_confirmatory_pcr_info['date_extracted']
        ) \
        .join(Sample).filter_by(
            sample_identifier=covid_confirmatory_pcr_info['sample_identifier']
        ) \
        .all()
    if len(matching_covid_confirmatory_pcr) == 0:
        return False
    elif len(matching_covid_confirmatory_pcr) == 1:
        return matching_covid_confirmatory_pcr[0]
    else:
        print(
            f"Getting covid confirmatory PCR. "
            f"More than one match for {covid_confirmatory_pcr_info['sample_identifier']} on date"
            f" {covid_confirmatory_pcr_info['date_covid_confirmatory_pcred']} with "
            f"covid_confirmatory_pcr_identifier {covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier']}. \n"
            f"This should not happen, exiting."
        )
        sys.exit(1)


def read_in_covid_confirmatory_pcr(covid_confirmatory_pcr_info: dict) -> CovidConfirmatoryPcr:
    """
    Read in a covid confirmatory pcr result into a CovidConfirmatoryPcr object.

    Args:
        covid_confirmatory_pcr_info (dict): a dictionary containing the covid confirmatory pcr
                                            result information

    Returns:
        CovidConfirmatoryPcr: the covid confirmatory pcr object
    """
    # Check covid_confirmatory_pcr_info has all the required fields
    check_empty_fields(
        covid_confirmatory_pcr_info,
        ['sample_identifier', 'date_extracted', 'extraction_identifier',
         'date_covid_confirmatory_pcred', 'covid_confirmatory_pcr_identifier',
         'group_name', 'covid_confirmatory_pcr_protocol']
    )
    covid_confirmatory_pcr = CovidConfirmatoryPcr()
    if covid_confirmatory_pcr_info['date_covid_confirmatory_pcred']:
        covid_confirmatory_pcr.date_pcred = covid_confirmatory_pcr_info['date_covid_confirmatory_pcred']
    if covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier']:
        covid_confirmatory_pcr.pcr_identifier = covid_confirmatory_pcr_info['covid_confirmatory_pcr_identifier']
    if covid_confirmatory_pcr_info['covid_confirmatory_pcr_protocol']:
        covid_confirmatory_pcr.protocol = covid_confirmatory_pcr_info['covid_confirmatory_pcr_protocol']
    if not covid_confirmatory_pcr_info['covid_confirmatory_pcr_ct']:
        covid_confirmatory_pcr.ct = None
    else:
        covid_confirmatory_pcr.ct = covid_confirmatory_pcr_info['covid_confirmatory_pcr_ct']

    return covid_confirmatory_pcr


def add_culture(culture_info: dict):
    """
    Add a culture to the database.

    Args:
        culture_info (dict): a dictionary containing the culture information
    """
    sample = get_sample(culture_info)
    if not sample:
        print(
            f"Adding culture, cant find sample for this result:\n"
            f"{culture_info['sample_identifier']} for {culture_info['group_name']}\n"
            f"Exiting."
        )
        sys.exit(1)
    culture = read_in_culture(culture_info)
    sample.cultures.append(culture)
    db.session.add(culture)
    db.session.commit()
    print(f"Adding culture for {culture_info['sample_identifier']} to database.")


def get_culture(culture_info: dict) -> Culture:
    """
    Get a culture from the database.

    Args:
        culture_info (dict): a dictionary containing the culture information
    
    Returns:
        Culture: the culture object, or False if there is no match
    """
    if 'culture_identifier' not in culture_info:
        return False

    matching_culture = Culture.query.filter_by(
            culture_identifier=culture_info['culture_identifier'],
            date_cultured=culture_info['date_cultured']
        ) \
        .join(Sample) \
        .filter_by(sample_identifier=culture_info['sample_identifier']) \
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
        print(
            f"Trying to get culture. \n"
            f"More than one Culture match for {culture_info['sample_identifier']}. \n"
            f"This should not happen, exiting."
        )
        sys.exit(1)


def read_in_culture(culture_info: dict) -> Culture:
    """
    Read in a culture into a Culture object.

    Args:
        culture_info (dict): a dictionary containing the culture information

    Returns:
        Culture: the culture object
    """
    if not check_cultures(culture_info):
        sys.exit(1)
    culture = Culture()
    culture.date_cultured = culture_info['date_cultured']
    culture.culture_identifier = culture_info['culture_identifier']
    # if the submitter_plate_id starts with SAM,
    #     then the culture is a culture that was created in the lab
    # if the submitter_plate_id starts with OUT,
    #     then the culture is an externally sequenced culture and has no submitter plate info
    if culture_info['submitter_plate_id'].startswith('CUL'):
        culture.submitter_plate_id = culture_info['submitter_plate_id']
        culture.submitter_plate_well = culture_info['submitter_plate_well']
    elif culture_info['submitter_plate_id'].startswith('OUT'):
        culture.submitter_plate_id = culture_info['submitter_plate_id']
        culture.submitter_plate_well = None
    return culture


def add_extraction(extraction_info: dict):
    """
    Add an extraction to the database.

    Args:
        extraction_info (dict): a dictionary containing the extraction information
    """
    extraction = read_in_extraction(extraction_info)
    if extraction_info['extraction_from'] == 'whole_sample':
        sample = get_sample(extraction_info)
        if not sample:
            print(
                f"Adding extraction. There is no matching sample with the sample_source_identifier "
                f"{extraction_info['sample_identifier']} for group {extraction_info['group_name']}, "
                f"please add using python seqbox_cmd.py add_sample and then re-run this command. \n"
                f"Exiting.")
            sys.exit(1)
        sample.extractions.append(extraction)
    elif extraction_info['extraction_from'] == 'cultured_isolate':
        culture = get_culture(extraction_info)
        if not culture:
            print(
                f"Adding extraction. There is no matching culture with the sample_source_identifier "
                f"{extraction_info['sample_identifier']} for group {extraction_info['group_name']}, "
                f"please add using python seqbox_cmd.py add_culture and then re-run this command. \n"
                f"Exiting."
            )
            sys.exit(1)
        culture.extractions.append(extraction)
    db.session.add(extraction)
    db.session.commit()
    print(
        f"Adding {extraction_info['sample_identifier']} extraction on "
        f"{extraction_info['date_extracted']} to the DB"
    )


def add_elution_info_to_extraction(elution_info: dict):
    """
    Add elution info to an extraction.

    Args:
        elution_info (dict): a dictionary containing the elution information
    """
    extraction = get_extraction(elution_info)
    if not extraction:
        print(
            f"Adding elution info. \n"
            f"No Extraction match for {elution_info['sample_identifier']}, extracted on "
            f"{elution_info['date_extracted']} for extraction id "
            f"{elution_info['extraction_identifier']} "
            f"need to add that extract and re-run. \nExiting."
        )
        sys.exit(1)
    assert elution_info['elution_plate_well'] in {
        'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12',
        'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12',
        'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12',
        'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12',
        'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12',
        'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
        'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10', 'G11', 'G12',
        'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11', 'H12'
    }
    extraction.elution_plate_id = elution_info['elution_plate_id']
    extraction.elution_plate_well = elution_info['elution_plate_well']
    #elution = read_in_elution(elution_info)
    #extraction.elutions.append(elution)
    #db.session.add(elution)
    db.session.commit()
    print(
        f"Adding elution info for {elution_info['sample_identifier']} extraction on "
        f"{elution_info['date_extracted']} to the DB"
    )


def get_extraction(readset_info: dict) -> Extraction:
    """
    Get an extraction from the database.

    Args:
        readset_info (dict): a dictionary containing the readset information
    
    Returns:
        Extraction: the extraction object, or False if there is no match
    """
    matching_extraction = None
    # TODO: - could replace this with a union query
    if readset_info['extraction_from'] == 'whole_sample':
        matching_extraction = Extraction.query.filter_by(
                extraction_identifier=readset_info['extraction_identifier'],
                date_extracted=readset_info['date_extracted']
            ) \
            .join(Sample) \
            .filter_by(sample_identifier=readset_info['sample_identifier']) \
            .join(SampleSource) \
            .join(SampleSource.projects) \
            .join(Groups) \
            .filter_by(group_name=readset_info['group_name']) \
            .all()
    elif readset_info['extraction_from'] == 'cultured_isolate':
        matching_extraction = Extraction.query.filter_by(
                extraction_identifier=readset_info['extraction_identifier'],
                date_extracted=readset_info['date_extracted']
            ) \
            .join(Culture) \
            .join(Sample) \
            .filter_by(sample_identifier=readset_info['sample_identifier']) \
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
        print(
            f"Trying to get extraction. \n"
            f"More than one Extraction match for {readset_info['sample_identifier']}. \n"
            f"This should not happen, exiting.")
        sys.exit(1)


def read_in_extraction(extraction_info: dict) -> Extraction:
    """
    Read in an extraction into an Extraction object.

    Args:
        extraction_info (dict): a dictionary containing the extraction information

    Returns:
        Extraction: the extraction object
    """
    extraction = Extraction()
    # TODO: Get rid of the 'if checks' because by this time we have already checked
    #           the validity extraction_info fields
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
    # we dont need nucleic_acid_concentration when it is an externally sequenced sample
    # (i.e. submitter_plate_id starts with OUT)
    if not extraction_info['submitter_plate_id'].startswith('OUT'):
        if extraction_info['nucleic_acid_concentration']:
            extraction.nucleic_acid_concentration = extraction_info['nucleic_acid_concentration']
    if extraction_info['submitter_plate_id'].startswith('EXT'):
        extraction.submitter_plate_id = extraction_info['submitter_plate_id']
        extraction.submitter_plate_well = extraction_info['submitter_plate_well']
    elif extraction_info['submitter_plate_id'].startswith('OUT'):
        extraction.submitter_plate_id = extraction_info['submitter_plate_id']
        extraction.submitter_plate_well = None
    return extraction


def add_group(group_info: dict) -> bool:
    """
    Add a group to the database.

    Args:
        group_info (dict): a dictionary containing the group information

    Returns:
        bool: True if the group was added, False if it already exists
    """
    matching_group = get_group(group_info)
    if matching_group:
        print(
            f"Not adding group {group_info['group_name']} from {group_info['institution']} "
            f"to database as it already exists."
        )
        return False
    group = read_in_group(group_info)
    db.session.add(group)
    db.session.commit()
    print(
        f"Adding group {group_info['group_name']} from {group_info['institution']} to database."
    )
    return True


def get_group(group_info: dict) -> Groups:
    """
    Get a group from the database.

    Args:
        group_info (dict): a dictionary containing the group information
    
    Returns:
        Groups: the group object, or False if there is no match
    """
    if 'group_name' not in group_info or 'institution' not in group_info:
        print(f"group_name and institution are required.")
        sys.exit(1)
    matching_group = Groups.query.filter_by(
            group_name=group_info['group_name'],
            institution=group_info['institution']
        ) \
        .all()
    if len(matching_group) == 0:
        return False
    elif len(matching_group) == 1:
        return matching_group[0]
    else:
        print(
            f"Getting group.\n"
            f"More than one match for {group_info['group_name']} from {group_info['institution']}.\n"
            f"This should not happen, exiting."
        )
        sys.exit(1)


def read_in_group(group_info: dict) -> Groups:
    """
    Read in a group into a Groups object.

    Args:
        group_info (dict): a dictionary containing the group information

    Returns:
        Groups: the group object
    """    
    # Check that the group name and institution are not empty, and group name does not contain
    # any invalid characters (spaces or slashes)
    check_empty_fields(group_info, ['group_name', 'institution'])
    check_invalid_characters([' ', '/'], group_info, 'group_name')
    group = Groups()
    group.group_name = group_info['group_name']
    group.institution = group_info['institution']
    group.pi = group_info['pi']
    return group


def add_mykrobe_result(mykrobe_result_info: dict):
    """
    Add a mykrobe result to the database.

    Args:
        mykrobe_result_info (dict): a dictionary containing the mykrobe result information
    """
    mykrobe_result_info = rename_dodgy_mykrobe_variables(mykrobe_result_info)
    readset = get_readset_from_readset_identifier(mykrobe_result_info)
    if not readset:
        print(
            f"Adding mykrobe result. \n"
            f"There is no matching readset with the readset_identifier "
            f"{mykrobe_result_info['readset_identifier']}, please add using "
            f"python seqbox_cmd.py add_readset and then re-run this command. \nExiting."
        )
        sys.exit(1)

    mykrobe = read_in_mykrobe(mykrobe_result_info)
    readset.mykrobes.append(mykrobe)
    db.session.add(mykrobe)
    db.session.commit()


def get_mykrobe_result(mykrobe_result_info: dict) -> Mykrobe:
    """
    Get a mykrobe result from the database.

    Args:
        mykrobe_result_info (dict): a dictionary containing the mykrobe result information

    Returns:
        Mykrobe: the mykrobe object, or False if there is no match
    """
    matching_mykrobe_result = Mykrobe.query \
        .filter_by(
            mykrobe_version=mykrobe_result_info['mykrobe_version'],
            drug=mykrobe_result_info['drug']
        ) \
        .join(ReadSet) \
        .filter_by(
            readset_identifier=mykrobe_result_info['readset_identifier']
        ).distinct().all()
    if len(matching_mykrobe_result) == 0:
        return False
    elif len(matching_mykrobe_result) == 1:
        return matching_mykrobe_result[0]
    else:
        print(
            f"Trying to get mykrobe_result. There is more than one matching mykrobe_result "
            f"with the sample_identifier {mykrobe_result_info['sample_identifier']} for "
            f"group {mykrobe_result_info['group_name']}. This shouldn't happen. Exiting."
        )
        sys.exit(1)


def read_in_mykrobe(mykrobe_result_info: dict) -> Mykrobe:
    """
    Read in a mykrobe result into a Mykrobe object.

    Args:
        mykrobe_result_info (dict): a dictionary containing the mykrobe result information

    Returns:
        Mykrobe: the mykrobe object
    """
    # Check that the required mykrobe results are not empty
    check_empty_fields(
        mykrobe_result_info, ['sample', 'drug', 'susceptibility', 'mykrobe_version']
    )
    mykrobe = Mykrobe()
    mykrobe.mykrobe_version = mykrobe_result_info['mykrobe_version']
    mykrobe.drug = mykrobe_result_info['drug']
    mykrobe.susceptibility = mykrobe_result_info['susceptibility']
    if mykrobe_result_info['variants']:
        mykrobe.variants = mykrobe_result_info['variants']
    if mykrobe_result_info['genes']:
        mykrobe.genes = mykrobe_result_info['genes']
    if mykrobe_result_info['phylo_group']:
        mykrobe.phylo_grp = mykrobe_result_info['phylo_group']
    if mykrobe_result_info['species']:
        mykrobe.species = mykrobe_result_info['species']
    if mykrobe_result_info['lineage']:
        mykrobe.lineage = mykrobe_result_info['lineage']
    if mykrobe_result_info['phylo_group_per_covg']:
        mykrobe.phylo_grp_covg = mykrobe_result_info['phylo_group_per_covg']
    if mykrobe_result_info['species_per_covg']:
        mykrobe.species_covg = mykrobe_result_info['species_per_covg']
    if mykrobe_result_info['lineage_per_covg']:
        mykrobe.lineage_covg = mykrobe_result_info['lineage_per_covg']
    if mykrobe_result_info['phylo_group_depth']:
        mykrobe.phylo_grp_depth = mykrobe_result_info['phylo_group_depth']
    if mykrobe_result_info['species_depth']:
        mykrobe.species_depth = mykrobe_result_info['species_depth']
    if mykrobe_result_info['lineage_depth']:
        mykrobe.lineage_depth = mykrobe_result_info['lineage_depth']
    return mykrobe


def add_pangolin_result(pangolin_result_info: dict):
    """
    Add a pangolin result to the database.

    Args:
        pangolin_result_info (dict): a dictionary containing the pangolin result information
    """
    artic_covid_result = get_artic_covid_result(pangolin_result_info)
    if not artic_covid_result:
        print(
            f"Warning - trying to add pangolin results. There is no readset for barcode "
            f"{pangolin_result_info['barcode']} from read set batch "
            f"{pangolin_result_info['readset_batch_name']}."
        )
        return False
    pangolin_result = read_in_pangolin_result(pangolin_result_info)
    artic_covid_result.pangolin_results.append(pangolin_result)
    db.session.commit()
    print(
        f"Adding pangolin_result {pangolin_result_info['taxon']} from "
        f"{pangolin_result_info['readset_batch_name']} to database."
    )


def get_pangolin_result(pangolin_result_info: dict) -> PangolinResult:
    """
    Get a pangolin result from the database.

    Args:
        pangolin_result_info (dict): a dictionary containing the pangolin result information

    Returns:
        PangolinResult: the pangolin result object, or False if there is no match
    """
    matching_pangolin_result = PangolinResult.query \
        .filter_by(version=pangolin_result_info['version']) \
        .join(ArticCovidResult) \
        .filter_by(
            profile=pangolin_result_info['artic_profile'],
            workflow=pangolin_result_info['artic_workflow']
        ) \
        .join(ReadSet) \
        .join(ReadSetBatch) \
        .filter_by(name=pangolin_result_info['readset_batch_name']) \
        .join(ReadSetNanopore) \
        .filter_by(barcode=pangolin_result_info['barcode']).all()
    if len(matching_pangolin_result) == 1:
        return matching_pangolin_result[0]
    elif len(matching_pangolin_result) == 0:
        return False
    else:
        print(
            f"Trying to get pangolin_result. \n"
            f"More than one PangolinResult for version {pangolin_result_info['version']} "
            f"barcode {pangolin_result_info['barcode']} for readset batch"
            f"{pangolin_result_info['readset_batch_name']}, run with profile "
            f"{pangolin_result_info['artic_profile']} and workflow "
            f"{pangolin_result_info['artic_workflow']}. \n"
            f"This should not happen. Exiting.")
        sys.exit(1)


def read_in_pangolin_result(pangolin_result_info: dict) -> PangolinResult:
    """
    Read in a pangolin result into a PangolinResult object.

    Args:
        pangolin_result_info (dict): a dictionary containing the pangolin result information

    Returns:
        PangolinResult: the pangolin result object
    """
    check_pangolin_result(pangolin_result_info)
    pangolin_result = PangolinResult()
    pangolin_result.lineage = pangolin_result_info['lineage']

    if 'conflict' not in pangolin_result_info or not pangolin_result_info['conflict']:
        pangolin_result.conflict = None
    else:
        pangolin_result.conflict = pangolin_result_info['conflict']
    if 'ambiguity_score' not in pangolin_result_info or not pangolin_result_info['ambiguity_score']:
        pangolin_result.ambiguity_score = None
    else:
        pangolin_result.ambiguity_score = pangolin_result_info['ambiguity_score']
    if 'scorpio_call' not in pangolin_result_info or not pangolin_result_info['scorpio_call']:
        pangolin_result.scorpio_call = None
    else:
        pangolin_result.scorpio_call = pangolin_result_info['scorpio_call']
    if 'scorpio_support' not in pangolin_result_info or not pangolin_result_info['scorpio_support']:
        pangolin_result.scorpio_support = None
    else:
        pangolin_result.scorpio_support = pangolin_result_info['scorpio_support']
    if 'scorpio_conflict' not in pangolin_result_info or not pangolin_result_info['scorpio_conflict']:
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


def add_pcr_assay(pcr_assay_info: dict):
    """
    Add a pcr assay to the database.

    Args:
        pcr_assay_info (dict): a dictionary containing the pcr assay information
    
    Returns:
        bool: True if the pcr assay was added, False if it already exists
    """
    if get_pcr_assay(pcr_assay_info) is not False:
        print(
            f"Adding pcr_assay {pcr_assay_info['assay_name']} to database as it already exists."
        )
        return False
    pcr_assay = PcrAssay()
    assert pcr_assay_info['assay_name'].strip() != ''
    pcr_assay.assay_name = pcr_assay_info['assay_name']
    db.session.add(pcr_assay)
    db.session.commit()
    print(f"Adding pcr_assay {pcr_assay_info['assay_name']} to database.")
    return True


def get_pcr_assay(pcr_assay_info: dict) -> PcrAssay:
    """
    Get a pcr assay from the database.

    Args:
        pcr_assay_info (dict): a dictionary containing the pcr assay information
    
    Returns:
        PcrAssay: the pcr assay object, or False if there is no match
    """
    matching_pcr_assay = PcrAssay.query.filter_by(
        assay_name=pcr_assay_info['assay_name']
    ).all()
    if len(matching_pcr_assay) == 0:
        return False
    elif len(matching_pcr_assay) == 1:
        return matching_pcr_assay[0]
    else:
        print(
            f"Getting pcr assay. Within getting pcr_result. \n"
            f"More than one match in the db for {pcr_assay_info['assay']}. \n"
            f"Shouldn't happen, exiting."
        )
        sys.exit(1)


def add_pcr_result(pcr_result_info: dict):
    """
    Add a pcr result to the database.

    Args:
        pcr_result_info (dict): a dictionary containing the pcr result information
    """
    if not check_pcr_result(pcr_result_info):
        sys.exit(1)
    if get_pcr_result(pcr_result_info):
        sys.exit(1)
    pcr_result = read_in_pcr_result(pcr_result_info)
    assay = get_pcr_assay(pcr_result_info)
    assay.pcr_results.append(pcr_result)
    sample = get_sample(pcr_result_info)
    if not sample:
        print(
            f"Adding pcr result, cant find sample for this result:\n{pcr_result_info}\nExiting."
        )
        sys.exit(1)
    sample.pcr_results.append(pcr_result)
    db.session.add(pcr_result)
    db.session.commit()
    print(
        f"Adding pcr_result for {pcr_result_info['sample_identifier']}, assay "
        f"{pcr_result_info['assay_name']} to database."
    )


def get_pcr_result(pcr_result_info: dict) -> PcrResult:
    """
    Get a pcr result from the database.

    Args:
        pcr_result_info (dict): a dictionary containing the pcr result information

    Returns:
        PcrResult: the pcr result object, or False if there is no match
    """
    assay = get_pcr_assay(pcr_result_info)
    if not assay:
        print(
            f"There is no pcr assay called {pcr_result_info['assay_name']} in the database, "
            f"please add it and re-run. \n"
            f"Exiting."
        )
        sys.exit(1)
    matching_pcr_result = PcrResult.query.filter_by(
            date_pcred=pcr_result_info['date_pcred'],
            pcr_identifier=pcr_result_info['pcr_identifier']
        ) \
        .join(PcrAssay) \
        .filter_by(assay_name=pcr_result_info['assay_name']) \
        .join(Sample) \
        .filter_by(sample_identifier=pcr_result_info['sample_identifier']).all()
    if len(matching_pcr_result) == 0:
        return False
    elif len(matching_pcr_result) == 1:
        return matching_pcr_result[0]
    else:
        print(
            f"Getting pcr result.\n"
            f"More than one match in the db for {pcr_result_info['sample_identifier']}, running"
            f"the {pcr_result_info['assay']} test, on {pcr_result_info['date_pcred']} \n"
            f"This should not happen, exiting."
        )
        sys.exit(1)


def read_in_pcr_result(pcr_result_info: dict) -> PcrResult:
    """
    Read in a pcr result into a PcrResult object.

    Args:
        pcr_result_info (dict): a dictionary containing the pcr result information

    Returns:
        PcrResult: the pcr result object
    """
    if not check_pcr_result(pcr_result_info):
        sys.exit(1)
    pcr_result = PcrResult()
    if pcr_result_info['date_pcred']:
        pcr_result.date_pcred = pcr_result_info['date_pcred']
    if pcr_result_info['pcr_identifier']:
        pcr_result.pcr_identifier = pcr_result_info['pcr_identifier']
    if not pcr_result_info['ct']:
        pcr_result.ct = None
    else:
        pcr_result.ct = pcr_result_info['ct']
    if pcr_result_info['pcr_result']:
        pcr_result.pcr_result = pcr_result_info['pcr_result']
    return pcr_result


def add_project(project_info: dict):
    """
    Add a project to the database.

    Args:
        project_info (dict): a dictionary containing the project information
    """
    group = get_group(project_info)
    if not group:
        print(
            f"Trying to get group to add project. \n"
            f"No group {project_info['group_name']} from institution "
            f"{project_info['institution']}.\n"
            f"You need to add this group. Exiting."
        )
        sys.exit(1)
    project = Project(
        project_name=project_info['project_name'],
        project_details=project_info['project_details']
    )
    group.projects.append(project)
    db.session.add(project)
    db.session.commit()
    print(
        f"Added project {project_info['project_name']} to group {project_info['group_name']} "
        f"at {project_info['institution']}."
    )


def get_projects(info: dict):
    """
    Get a list of projects from the database.

    Args:
        info (dict): a dictionary containing the group information
    """
    assert 'projects' in info
    assert 'group_name' in info
    project_names = [x.strip() for x in info['projects'].split(';')]
    projects = []
    for project_name in project_names:
        p = query_projects(info, project_name)
        if p[0]:
            projects.append(p[1])
        elif not p[0]:
            print(
                f"Getting projects. Project {project_name} from group {info['group_name']} "
                f"does not exist in the db, you need to add it using the seqbox_cmd.py "
                f"add_projects function.\nExiting now."
            )
            sys.exit(1)
    return projects


def query_projects(info: dict, project_name: str) -> tuple:
    """
    Query the database for a project by name.

    Args:
        info (dict): a dictionary containing the group information
        project_name (str): the name of the project to query

    Returns:
        tuple: (True, project) if the project exists, (False,) if it does not
    """
    matching_projects = Project.query.filter_by(project_name=project_name) \
        .join(Groups) \
        .filter_by(group_name=info['group_name'], institution=info['institution']).all()
    if len(matching_projects) == 0:
        # need this to have the `,` so that can evaluate the return correctly for the elif section
        return False,
    elif len(matching_projects) == 1:
        s = matching_projects[0]
        return True, s
    else:
        print(
            f"Querying projects. \n"
            f"There is already more than one project called {project_name} from "
            f"{info['group_name']} at {info['institution']} in the database.\n"
            f"This should not happen. Exiting."
        )
        sys.exit(1)


def get_raw_sequencing_batch(batch_name: str) -> RawSequencingBatch:
    """
    Get a raw sequencing batch from the database.

    Args:
        batch_name (str): the name of the raw sequencing batch
    """
    matching_raw_seq_batch = RawSequencingBatch.query.filter_by(name=batch_name).all()
    if len(matching_raw_seq_batch) == 1:
        return matching_raw_seq_batch[0]
    elif len(matching_raw_seq_batch) == 0:
        return False
    else:
        print(
            f"Getting raw_sequencing batch. More than one match for {batch_name}. \n"
            f"This should not happen, exiting."
        )
        sys.exit(1)


def get_raw_sequencing(readset_info: dict, raw_sequencing_batch: RawSequencingBatch, covid: bool) -> RawSequencing:
    """
    Get a raw sequencing from the database.

    Args:
        readset_info (dict): a dictionary containing the readset information
        raw_sequencing_batch (RawSequencingBatch): the raw sequencing batch object
        covid (bool): True if the raw sequencing is covid, False if it is not
    
    Returns:
        RawSequencing: the raw sequencing object, or False if there is no match
    """
    if covid:
        matching_raw_sequencing = RawSequencing.query \
            .join(RawSequencingBatch) \
            .filter_by(name=raw_sequencing_batch.name) \
            .join(TilingPcr) \
            .filter_by(
                pcr_identifier=readset_info['tiling_pcr_identifier'],
                date_pcred=readset_info['date_tiling_pcred']
            ) \
            .join(Extraction) \
            .join(Sample) \
            .filter_by(sample_identifier=readset_info['sample_identifier']) \
            .join(SampleSource) \
            .join(SampleSource.projects) \
            .join(Groups) \
            .filter_by(group_name=readset_info['group_name']) \
            .all()
    elif not covid:
        matching_raw_sequencing = RawSequencing.query \
            .join(RawSequencingBatch) \
            .filter_by(name=raw_sequencing_batch.name) \
            .join(Extraction) \
            .filter_by(
                date_extracted=readset_info['date_extracted'],
                extraction_identifier=readset_info['extraction_identifier']
            ) \
            .filter(Extraction.submitter_plate_id.is_not(None)) \
            .join(Sample) \
            .filter_by(sample_identifier=readset_info['sample_identifier']) \
            .join(SampleSource) \
            .join(SampleSource.projects) \
            .join(Groups) \
            .filter_by(group_name=readset_info['group_name']) \
            .distinct() \
            .union(
                RawSequencing.query \
                    .join(RawSequencingBatch) \
                    .filter_by(name=raw_sequencing_batch.name) \
                    .join(Extraction) \
                    .filter_by(
                        date_extracted=readset_info['date_extracted'],
                        extraction_identifier=readset_info['extraction_identifier']
                    ) \
                    .join(Culture) \
                    .filter(Culture.submitter_plate_id.is_not(None)) \
                    .join(Sample) \
                    .filter_by(sample_identifier=readset_info['sample_identifier']) \
                    .join(SampleSource) \
                    .join(SampleSource.projects) \
                    .join(Groups) \
                    .filter_by(group_name=readset_info['group_name']) \
                    .distinct()
            ).all()
    if len(matching_raw_sequencing) == 0:
        # no matching raw sequencing will be the case for 99.999% of illumina
        # (all illumina?) and most nanopore
        return False
    elif len(matching_raw_sequencing) == 1:
        # if there is already a raw_sequencing record (i.e. this is another basecalling run
        # of the same raw_sequencing data), then extraction is already associated with the
        # raw sequencing, so don't need to add.
        # TODO - add in asserts checking that thing returning matches the queries in order
        #        to guard against poorly written queries
        # assert matching_raw_sequencing[0].tiling_pcr.tiling_pcr_identifier == readset_info['tiling_pcr_identifier']
        # assert matching_raw_sequencing[0].tiling_pcr.date_pcred == readset_info['date_tiling_pcred']
        # assert matching_raw_sequencing[0].extraction.sample.sample_identifier == readset_info['sample_identifier']
        # assert matching_raw_sequencing[0].extraction.sample.projects.group_name == readset_info['group_name']
        return matching_raw_sequencing[0]
    else:
        print(
            f"Getting raw_sequencing, more than one match in {readset_info['batch']} for sample "
            f"{readset_info['sample_identifier']} from group {readset_info['group_name']}.\n"
            f"This should not happen, exiting."
        )


def add_raw_sequencing_batch(raw_sequencing_batch_info: dict):
    """
    Add a raw sequencing batch to the database.

    Args:
        raw_sequencing_batch_info (dict): a dictionary containing the raw sequencing batch 
                                          information
    """
    raw_sequencing_batch = read_in_raw_sequencing_batch_info(raw_sequencing_batch_info)
    db.session.add(raw_sequencing_batch)
    db.session.commit()
    print(f"Added raw sequencing batch {raw_sequencing_batch_info['batch_name']} to the database.")


def read_in_raw_sequencing(
        readset_info: dict, nanopore_default: bool, sequencing_type: str, batch_directory: str
    ) -> RawSequencing:
    """
    Read in a raw sequencing into a RawSequencing object.

    Args:
        readset_info (dict): a dictionary containing the readset information
        nanopore_default (bool): True if the readset follows standard nanopore formatting
        sequencing_type (str): the sequencing type (nanopore or illumina)
        batch_directory (str): the path to the raw sequencing batch directory

    Returns:
        RawSequencing: the raw sequencing object
    """
    raw_sequencing = RawSequencing()
    if sequencing_type == 'illumina':
        raw_sequencing.raw_sequencing_illumina = RawSequencingIllumina()
        # not taking the read paths from the input file anymore, will get them from the
        # inbox_from_config/batch/sample_name
        #raw_sequencing.raw_sequencing_illumina.path_r1 = readset_info['path_r1']
        #raw_sequencing.raw_sequencing_illumina.path_r2 = readset_info['path_r2']
        # if the readset is externally sequenced,
        #     then the submitter_readset_id will start with OUT, and
        # we don't want to add the library prep method
        if not readset_info['submitter_plate_id'].startswith('OUT'):
            raw_sequencing.raw_sequencing_illumina.library_prep_method = readset_info['library_prep_method']
    if sequencing_type == 'nanopore':
        raw_sequencing.raw_sequencing_nanopore = RawSequencingNanopore()
        if nanopore_default:
            path = os.path.join(batch_directory, 'fast5_pass', readset_info['barcode'], '*fast5')
            raw_sequencing.raw_sequencing_nanopore.path_fast5 = path
            raw_sequencing.raw_sequencing_nanopore.library_prep_method = readset_info['library_prep_method']
            fast5s = glob.glob(path)
            if len(fast5s) == 0:
                print(f'Warning - No fast5 found in {path}. Continuing, but check this.')
        elif not nanopore_default:
            assert readset_info['path_fast5'].endswith('fast5')
            assert os.path.isfile(readset_info['path_fast5'])
            raw_sequencing.raw_sequencing_nanopore.path_fast5 = readset_info['path_fast5']
        # raw_sequencing.raw_sequencing_nanopore.append(raw_sequencing_nanopore)
    return raw_sequencing


def read_in_raw_sequencing_batch_info(raw_sequencing_batch_info: dict) -> RawSequencingBatch:
    """
    Read in a raw sequencing batch into a RawSequencingBatch object.

    Args:
        raw_sequencing_batch_info (dict): a dictionary containing the raw sequencing batch 
                                          information

    Returns:
        RawSequencingBatch: the raw sequencing batch object
    """    
    # Check that all of the required fields are present
    check_empty_fields(
        raw_sequencing_batch_info,
        ['batch_directory', 'batch_name', 'date_run', 'sequencing_type',
        'instrument_name', 'flowcell_type'],
    )
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


def add_readset(readset_info: dict, covid: bool, nanopore_default: bool):
    """
    Add a readset to the database.

    Args:
        readset_info (dict): a dictionary containing the readset information
        covid (bool): True if the readset is covid, False if it is not
        nanopore_default (bool): True if the readset follows standard nanopore formatting
    """
    # this function has three main parts
    # 1. get the raw_sequencing batch
    # 2. get the extraction
    # 3. get the raw_sequencing
    #    a. if the raw sequencing doesn't already exist, make it and add it to extraction.
    readset_batch = get_readset_batch(readset_info)
    if not readset_batch:
        print(
            f"Adding readset. No ReadSetBatch match for {readset_info['readset_batch_name']}, "
            f"need to add that batch and re-run. \nExiting."
        )
        sys.exit(1)
    # this get_raw_sequencing_batch is probably superfluous, because the readset_batch should
    #  be guaranteed to have a raw_sequencing_batch attribute, and can then just be replaced
    #  with an assertion that it's true but will leave it in for now.
    # assert isinstance(readset_batch.raw_sequencing_batch, RawSequencingBatch)
    raw_sequencing_batch = get_raw_sequencing_batch(readset_batch.raw_sequencing_batch.name)
    if not raw_sequencing_batch:
        print(
            f"Adding readset. No RawSequencingBatch match for {readset_info['batch']}, need "
            f"to add that batch and re-run. \nExiting."
        )
        sys.exit(1)

    # get raw sequencing
    raw_sequencing = get_raw_sequencing(readset_info, readset_batch.raw_sequencing_batch, covid)

    # raw_sequencing will only be True if this is a re-basecalled readset
    if not raw_sequencing:
        # if it's false, means need to add raw sequencing
        raw_sequencing = read_in_raw_sequencing(
            readset_info,
            nanopore_default,
            raw_sequencing_batch.sequencing_type,
            raw_sequencing_batch.batch_directory
        )

        # need to add raw_seq to raw seq batch
        raw_sequencing_batch.raw_sequencings.append(raw_sequencing)
        if covid:
            # if the sample is covid, we need to get the tiling pcr record
            tiling_pcr = get_tiling_pcr(readset_info)
            if not tiling_pcr:
                print(
                    f"Adding readset. There is no TilingPcr record for sample "
                    f"{readset_info['sample_identifier']} PCRed on "
                    f"{readset_info['date_tiling_pcred']} by group {readset_info['group_name']}.\n"
                    f"You need to add this. Exiting.")
                sys.exit(1)

            # add the raw_seq to the tiling pcr
            tiling_pcr.raw_sequencings.append(raw_sequencing)

            # then add the raw sequencing to the extraction which was used to generate the
            # PCR as well.
            tiling_pcr.extraction.raw_sequencing.append(raw_sequencing)
        elif not covid:
            # if it's not covid, don't need the tiling pcr part, so just get the extractions
            extraction = get_extraction(readset_info)
            if not extraction:
                print(
                    f"Adding readset. No Extraction match for {readset_info['sample_identifier']},"
                    f"extracted on {readset_info['date_extracted']} for extraction id "
                    f"{readset_info['extraction_identifier']} need to add that extract and"
                    f"re-run. \nExiting."
                )
                sys.exit(1)
            # and add the raw_sequencing to the extraction
            extraction.raw_sequencing.append(raw_sequencing)


    # after having either got the raw_sequencing if this is a re-basecalled set, or read in
    # the raw_sequencing if it is not, it's time to read in the readset.
    readset = read_in_readset(
        readset_info,
        nanopore_default,
        raw_sequencing_batch,
        readset_batch,
        covid
    )
    readset_batch.readsets.append(readset)
    raw_sequencing.readsets.append(readset)

    # add the readset to the file structure
    db.session.add(raw_sequencing)
    db.session.commit()
    print(f"Added readset {readset_info['sample_identifier']} to the database.")


def add_readset_batch(readset_batch_info: dict):
    """
    Add a readset batch to the database.

    Args:
        readset_batch_info (dict): a dictionary containing the readset batch information
    """
    raw_sequencing_batch = get_raw_sequencing_batch(
        readset_batch_info['raw_sequencing_batch_name']
    )
    if not raw_sequencing_batch:
        print(
            f"Trying to get raw sequencing batch to add read set batch. \n"
            f"No raw sequencing batch {readset_batch_info['raw_sequencing_batch_name']}. \n"
            f"You need to add this raw sequencing batch. Exiting."
        )
        sys.exit(1)
    readset_batch = read_in_readset_batch(readset_batch_info)
    raw_sequencing_batch.readset_batches.append(readset_batch)
    db.session.commit()
    print(f"Added readset batch {readset_batch_info['raw_sequencing_batch_name']}.")


def get_readset(readset_info: dict, covid: bool) -> ReadSet:
    """
    Get a readset from the database.

    Args:
        readset_info (dict): a dictionary containing the readset information
        covid (bool): True if the readset is covid, False if it is not
    """
    # first we get the readset batch so that we can get the raw sequencing batch so that
    # we can get the sequencing type
    readset_batch = get_readset_batch(readset_info)
    if not readset_batch:
        print(
            f"Getting readset. No ReadSetBatch match for {readset_info['readset_batch_name']}, "
            f"need to add that batch and re-run. \nExiting.")
        sys.exit(1)
    # this get_raw_sequencing_batch is probably superfluous, because the readset_batch should
    # be guaranteed to have a raw_sequencing_batch attribute, and can then just be replaced
    # with an assertion that it's true but will leave it in for now.
    # assert isinstance(readset_batch.raw_sequencing_batch, RawSequencingBatch)
    # then,  we need to get the batch to see what kind of sequencing it is
    raw_sequencing_batch = get_raw_sequencing_batch(readset_batch.raw_sequencing_batch.name)
    if not raw_sequencing_batch:
        print(
            f"Getting readset. No RawSequencingBatch match for {readset_info['readset_batch_name']}, "
            f"need to add that batch and re-run. \nExiting.")
        sys.exit(1)

    readset_type = None
    # this is because the readset query is currently generic to sequencing type, so we use
    # this structure to cut down on duplicate code (otherwise, would need all of the below
    # for both illumina and nanopore). 
    # 
    # can probably just do this with readset_batch.raw_sequencing_batch.sequencing_type == 'illumina'
    if raw_sequencing_batch.sequencing_type == 'illumina':
        readset_type = ReadSetIllumina
    elif raw_sequencing_batch.sequencing_type == 'nanopore':
        readset_type = ReadSetNanopore
    # TODO - is this going to be a slow query when readset_ill/nano get big?
    #        if the sample is not covid, then need to match against the extraction
    # 
    # TODO - none of the tests here are actually for readset, they're all for rsb and above.
    #        to cover new basecalling runs of same raw sequencing, need to test for whether
    #        the fastq is already in the database.
    #
    # so - if it's nanopore default, need to construct the fastq path from rsb.batch_dir, barcode, fastq
    #  (should spin out the get fastq path functionality from add readset to filesystem into sep func)
    # if it's nanopore, but not default, the fastq path will be in the readset_info.
    # then, if it's nanopore, then filter the read_set_nanopore by the fastq path.
    # TODO - replace these combined queries with a union query going through tiling pcr for COVID,
    #        and then can get rid of the covid flag for this function (i think).
    if not covid:
        matching_readset = readset_type.query.join(ReadSet)\
            .join(ReadSetBatch) \
            .filter_by(name=readset_info['readset_batch_name'])\
            .join(RawSequencing) \
            .join(Extraction) \
            .filter_by(
                date_extracted=readset_info['date_extracted'],
                extraction_identifier=readset_info['extraction_identifier']
            ) \
            .filter(Extraction.submitter_plate_id.is_not(None)) \
            .join(Sample) \
            .filter_by(sample_identifier=readset_info['sample_identifier'])\
            .join(SampleSource)\
            .join(SampleSource.projects) \
            .join(Groups)\
            .filter_by(group_name=readset_info['group_name'])\
            .distinct() \
            .union(
                readset_type.query \
                    .join(ReadSet) \
                    .join(ReadSetBatch) \
                    .filter_by(name=readset_info['readset_batch_name']) \
                    .join(RawSequencing) \
                    .join(Extraction) \
                    .filter_by(
                        date_extracted=readset_info['date_extracted'],
                        extraction_identifier=readset_info['extraction_identifier']
                    ) \
                    .join(Culture) \
                    .filter(Culture.submitter_plate_id.is_not(None)) \
                    .join(Sample) \
                    .filter_by(sample_identifier=readset_info['sample_identifier']) \
                    .join(SampleSource) \
                    .join(SampleSource.projects) \
                    .join(Groups) \
                    .filter_by(group_name=readset_info['group_name']) \
                    .distinct()
            ).all()
    # if the sample is covid, then need to match against the tiling pcr
    elif covid:
        matching_readset = readset_type.query.join(ReadSet)\
            .join(ReadSetBatch) \
            .filter_by(name=readset_info['readset_batch_name']) \
            .join(RawSequencing) \
            .join(TilingPcr).filter_by(
                date_pcred=readset_info['date_tiling_pcred'],
                pcr_identifier=readset_info['tiling_pcr_identifier']
            ) \
            .join(Extraction)\
            .join(Sample) \
            .filter_by(sample_identifier=readset_info['sample_identifier']) \
            .join(SampleSource) \
            .join(SampleSource.projects) \
            .join(Groups) \
            .filter_by(group_name=readset_info['group_name']) \
            .distinct() \
            .all()
    # if there is no matching readset, return False
    if len(matching_readset) == 0:
        return False
    elif len(matching_readset) == 1:
        return matching_readset[0]
    else:
        print(
            f"Getting readset. More than one match for {readset_info['readset_batch_name']}. \n"
            f"Shouldn't happen, exiting."
        )
        sys.exit(1)


def get_readset_batch(readset_batch_info: dict) -> ReadSetBatch:
    """
    Get a readset batch from the database.

    Args:
        readset_batch_info (dict): a dictionary containing the readset batch information

    Returns:
        ReadSetBatch: the readset batch object, or False if there is no match
    """
    matching_readset_batch = ReadSetBatch.query.filter_by(
        name=readset_batch_info['readset_batch_name']
    ).all()
    if len(matching_readset_batch) == 0:
        return False
    elif len(matching_readset_batch) == 1:
        return matching_readset_batch[0]
    else:
        print(
            f"Getting readset batch. \n"
            f"More than one match for {readset_batch_info['readset_batch_name']}. \n"
            f"This should not happen, exiting."
        )
        sys.exit(1)


def get_readset_from_readset_identifier(readset_info: dict) -> ReadSet:
    """
    Get a readset from the database.

    Args:
        readset_info (dict): a dictionary containing the readset information

    Returns:
        ReadSet: the readset object, or False if there is no match
    """
    matching_readset = ReadSet.query.filter_by(
        readset_identifier=readset_info['readset_identifier']
    ).all()
    if len(matching_readset) == 0:
        return False
    elif len(matching_readset) == 1:
        return matching_readset[0]
    else:
        print(
            f"Getting readset. "
            f"More than one match for {readset_info['readset_identifier']}. "
            f"This should not happen, exiting."
        )
        sys.exit(1)


def get_nanopore_readset_from_batch_and_barcode(batch_and_barcode_info: dict) -> ReadSetNanopore:
    """
    Get a nanopore readset from the database.

    Args:
        batch_and_barcode_info (dict): a dictionary containing the batch and barcode information

    Returns:
        ReadSetNanopore: the nanopore readset object, or False if there is no match
    """
    matching_readset = ReadSetNanopore.query \
        .filter_by(
            barcode=batch_and_barcode_info['barcode']
        ) \
        .join(ReadSet) \
        .join(ReadSetBatch) \
        .filter_by(name=batch_and_barcode_info['readset_batch_name']) \
        .all()
    if len(matching_readset) == 0:
        return False
    elif len(matching_readset) == 1:
        return matching_readset[0]


def read_in_readset(
        readset_info: dict,
        nanopore_default: bool,
        raw_sequencing_batch: RawSequencingBatch,
        readset_batch: ReadSetBatch,
        covid: bool) -> ReadSet:
    """
    Read in a readset into a ReadSet object.

    Args:
        readset_info (dict): a dictionary containing the readset information
        nanopore_default (bool): True if the readset follows standard nanopore formatting
        raw_sequencing_batch (RawSequencingBatch): the raw sequencing batch object
        readset_batch (ReadSetBatch): the readset batch object
        covid (bool): True if the readset is covid, False if it is not
    
    Returns:
        ReadSet: the readset object
    """
    readset = ReadSet()
    check_readset_fields(readset_info, nanopore_default, raw_sequencing_batch, covid)
    readset.data_storage_device = readset_info['data_storage_device']
    # usually there will be no sequencing_institution in the input file, but if there is,
    # it will be used. the default in the database is MLW. so for externally sequenced things,
    # we include sequencing_institution in the input file.
    if 'sequencing_institution' in readset_info:
        readset.sequencing_institution = readset_info['sequencing_institution']
    if raw_sequencing_batch.sequencing_type == 'nanopore':
        readset.readset_nanopore = ReadSetNanopore()
        if not nanopore_default:
            assert readset_info['path_fastq'].endswith('fastq.gz')
            readset.readset_nanopore.path_fastq = readset_info['path_fastq']
        elif nanopore_default:
            readset.readset_nanopore.barcode = readset_info['barcode']
            path = os.path.join(
                readset_batch.batch_directory,
                'fastq_pass',
                readset_info['barcode'],
                '*fastq.gz'
            )
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
        # not taking the read paths from the input file anymore, will get them from the
        # inbox_from_config/batch/sample_name
        readset.readset_illumina = ReadSetIllumina()
        #assert readset_info['path_r1'].endswith('fastq.gz')
        #assert readset_info['path_r2'].endswith('fastq.gz')
        #readset.readset_illumina.path_r1 = readset_info['path_r1']
        #readset.readset_illumina.path_r2 = readset_info['path_r2']
        return readset


def read_in_readset_batch(readset_batch_info: dict) -> ReadSetBatch:
    """
    Read in a readset batch into a ReadSetBatch object.

    Args:
        readset_batch_info (dict): a dictionary containing the readset batch information
    
    Returns:
        ReadSetBatch: the readset batch object
    """
    # Check readset_info_info for all of the required fields
    check_empty_fields(
        readset_batch_info,
        ['raw_sequencing_batch_name', 'readset_batch_name', 'readset_batch_dir', 'basecaller'],
    )
    readset_batch = ReadSetBatch()
    readset_batch.name = readset_batch_info['readset_batch_name']
    readset_batch.batch_directory = readset_batch_info['readset_batch_dir']
    readset_batch.basecaller = readset_batch_info['basecaller']
    return readset_batch


def add_sample(sample_info: dict, submitted_for_sequencing: bool):
    """
    Add a sample to the database.

    Args:
        sample_info (dict): a dictionary containing the sample information
        submitted_for_sequencing (bool): True if the sample has been submitted for sequencing
    """
    # sample_info is a dict of one line of the input csv (keys from col header)
    # for the projects listed in the csv, check if they already exist for that group
    # if it does, return it, if it does not, instantiate a new Project and return it
    check_samples(sample_info)
    sample_source = get_sample_source(sample_info)
    if not sample_source:
        print(
            f"Adding sample. \n"
            f"There is no matching sample_source with the sample_source_identifier "
            f"{sample_info['sample_source_identifier']} for group {sample_info['group_name']}, "
            f"please add using python seqbox_cmd.py add_sample_source and then re-run this command.\n"
            f"Exiting."
        )
        sys.exit(1)

    # instantiate a new Sample
    sample = read_in_sample_info(sample_info, submitted_for_sequencing)
    sample_source.samples.append(sample)
    sample.submitted_for_sequencing = submitted_for_sequencing
    db.session.add(sample)
    db.session.commit()
    print(f"Adding sample {sample_info['sample_identifier']}")


def add_sample_source(sample_source_info: dict) -> bool:
    """
    Add a sample source to the database.

    Args:
        sample_source_info (dict): a dictionary containing the sample source information

    Returns:
        bool: True if all data included, False missing data
    """
    # sample_info is a dict of one line of the input csv (keys from col header)
    # for the projects listed in the csv, check if they already exist for that group
    # if it does, return it, if it does not, instantiate a new Project and return it
    if 'sample_source_identifier' not in sample_source_info:
        print(f"Adding sample_source. sample_source missing critical information.")
        return False
    if get_sample_source(sample_source_info) is not False:
        print(
            f"Adding sample_source. sample_source {sample_source_info['sample_source_identifier']} "
            f"already exists in the database."
        )
        return False

    projects = get_projects(sample_source_info)

    # instantiate a new SampleSource
    sample_source = read_in_sample_source_info(sample_source_info)
    sample_source.projects = projects
    db.session.add(sample_source)
    db.session.commit()
    print(
        f"Adding sample_source {sample_source_info['sample_source_identifier']} to project(s) "
        f"{projects}"
    )
    return True


def get_sample_source(sample_info: dict) -> SampleSource:
    """
    Get a sample source from the database.

    Args:
        sample_info (dict): a dictionary containing the sample information

    Returns:
        SampleSource: the sample source object, or False if there is no match
    """
    # Want to find whether this sample_source is already part of this project
    # ensure that sample_info['sample_source_identifier']) is always interpreted by
    # the database as a char var, not an int this is because the sample_source_identifier
    # is a char field in the db, and if you pass an int, it will try to convert it to a char,
    # and then it will fail to find the sample_source.
    matching_sample_source = SampleSource.query.\
        filter_by(
            sample_source_identifier=str(sample_info['sample_source_identifier'])
        ) \
        .join(SampleSource.projects) \
        .join(Groups) \
        .filter_by(
            group_name=sample_info['group_name']
        ).all()
    if len(matching_sample_source) == 0:
        return False
    elif len(matching_sample_source) == 1:
        return matching_sample_source[0]
    else:
        print(
            f"Trying to get sample_source. \n"
            f"There is more than one matching sample_source with the sample_source_identifier "
            f"{sample_info['sample_source_identifier']} for group {sample_info['group_name']}, "
            f"This should not happen.\n"
            f"Exiting."
        )


def get_sample(readset_info: dict) -> Sample:
    """
    Get a sample from the database.

    Args:
        readset_info (dict): a dictionary containing the readset information

    Returns:
        Sample: the sample object, or False if there is no match
    """
    matching_sample = Sample.query \
        .filter_by(
            sample_identifier=readset_info['sample_identifier']
        ) \
        .join(SampleSource) \
        .join(SampleSource.projects) \
        .join(Groups) \
        .filter_by(
            group_name=readset_info['group_name']
        ) \
        .distinct() \
        .all()
    if len(matching_sample) == 0:
        return False
    elif len(matching_sample) == 1:
        return matching_sample[0]
    else:
        print(
            f"Trying to get sample. There is more than one matching sample with the "
            f"sample_identifier {readset_info['sample_identifier']} for group "
            f"{readset_info['group_name']}\n"
            f"This should not happen. Exiting.")
        sys.exit(1)


def query_info_on_covid_samples(args):
    """
    Query information on all covid samples in the database.
    """
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    # from here https://stackoverflow.com/questions/43459182/proper-sqlalchemy-use-in-flask
    engine = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    s = Session()
    # we filter on Sample.submitter_plate_id because all the covid samples are submitted as
    # samples, and then extracts are made, so the submitter plate is the sample plate.
    query_output = s.query(
            Sample,
            Groups.group_name,
            Groups.institution,
            Project.project_name,
            Sample.sample_identifier,
            Sample.day_received,
            Sample.month_received,
            Sample.year_received,
            PcrResult.pcr_result,
            PcrResult.ct,
            Sample.species,
            Sample.sequencing_type_requested,
            Sample.submitter_plate_id,
            Sample.submitter_plate_well,
            Extraction.elution_plate_id,
            Extraction.elution_plate_well,
            Extraction.date_extracted,
            Extraction.extraction_identifier,
            Extraction.nucleic_acid_concentration,
            CovidConfirmatoryPcr.date_pcred,
            CovidConfirmatoryPcr.ct,
            TilingPcr.date_pcred,
            TilingPcr.pcr_identifier,
            ReadSet.readset_identifier,
            ArticCovidResult.pct_covered_bases
        ) \
        .filter(Sample.species == 'SARS-CoV-2') \
        .filter(Sample.submitter_plate_id.is_not(None)) \
        .join(PcrResult, isouter=True) \
        .filter(PcrResult.pcr_result.startswith('Positive')) \
        .join(SampleSource) \
        .join(SampleSource.projects) \
        .join(Groups) \
        .join(Extraction, isouter=True) \
        .join(CovidConfirmatoryPcr, isouter=True) \
        .join(TilingPcr, isouter=True) \
        .join(RawSequencing, isouter=True) \
        .join(ReadSet, isouter=True) \
        .join(ReadSetBatch, isouter=True) \
        .join(ArticCovidResult, isouter=True) \
        .order_by(
            Sample.year_received,
            Sample.month_received,
            Sample.day_received,
            Sample.sample_identifier
        ).all()
    # print(query_output)
    allowed_project_names = {'ISARIC', 'COCOA', 'COCOSU', 'MARVELS'}
    header = [
        'group_name', 'institution', 'project_name', 'sample_identifier', 'day_received',
        'month_received', 'year_received', 'original_pcr_result', 'original_pcr_ct', 'species',
        'sequencing_type_requested', 'submitter_plate_id', 'submitter_plate_well',
        'elution_plate_id', 'elution_plate_well', 'date_extracted', 'extraction_identifier',
        'nucleic_acid_concentration', 'confirmatory_pcr_date', 'confirmatory_pcr_ct',
        'date_tiling_pcred', 'tiling_pcr_identifier', 'readset_identifier', 'pct_covered_bases'
    ]
    print(*header, sep='\t')
    for x in query_output:
        # print(x)
        # assert len(header) + 1 == len(x), f'header length is {len(header)} and x length is {len(x)}'
        if x[3] in allowed_project_names:
            print('\t'.join([str(y) for y in x[1:]]))
    # TODO - do the project name filtering in the query outcome parsing


def query_info_on_all_samples(args):
    """
    Query information on all samples in the database.
    """
    # at the moment args just being passed through in case needs to be used in future
    # need to use the sqlalchemy native option rather than the flask-sqlalchemy option
    # as the latter doesn't nicely return the join, have to do it manually from the
    # results (?i think?)
    SQLALCHEMY_DATABASE_URI = os.environ['DATABASE_URL']
    # from here https://stackoverflow.com/questions/43459182/proper-sqlalchemy-use-in-flask
    engine = sqlalchemy.create_engine(SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    s = Session()
    # need to do a union query to get samples from both the sample-culture-extract,
    # sample-extract paths, and just samples (i.e. whole samples submitted for extraction).
    #
    # the filter(Culture.submitter_plate_id.is_not(None)) and
    #     filter(Extraction.submitter_plate_id.is_not(None))
    # are to ensure that samples from the other path are not included in the results of the
    # query (i.e. samples that are None for Culture.submitter_plate_id will be ones where
    # the submitter gave in extracts, and that hence so sample-extract).
    sample_culture_extract = s.query(
            Sample,
            Groups.group_name,
            Groups.institution,
            Project.project_name,
            Sample.sample_identifier,
            Sample.species,
            Sample.sequencing_type_requested,
            Culture.submitter_plate_id,
            Culture.submitter_plate_well,
            Extraction.elution_plate_id,
            Extraction.elution_plate_well,
            Extraction.date_extracted,
            Extraction.extraction_identifier,
            Extraction.nucleic_acid_concentration,
            TilingPcr.date_pcred,
            TilingPcr.pcr_identifier,
            ReadSet.readset_identifier
        ) \
        .join(SampleSource) \
        .join(SampleSource.projects) \
        .join(Groups) \
        .join(Culture, isouter=True) \
        .filter(Culture.submitter_plate_id.is_not(None)) \
        .join(Extraction, isouter=True) \
        .join(TilingPcr, isouter=True) \
        .join(RawSequencing, isouter=True) \
        .join(ReadSet, isouter=True)
    #samples = [r._asdict() for r in samples]
    sample_extract = s.query(
            Sample,
            Groups.group_name,
            Groups.institution,
            Project.project_name,
            Sample.sample_identifier,
            Sample.species,
            Sample.sequencing_type_requested,
            Extraction.submitter_plate_id,
            Extraction.submitter_plate_well,
            Extraction.elution_plate_id,
            Extraction.elution_plate_well,
            Extraction.date_extracted,
            Extraction.extraction_identifier,
            Extraction.nucleic_acid_concentration,
            TilingPcr.date_pcred,
            TilingPcr.pcr_identifier,
            ReadSet.readset_identifier
        ) \
        .join(SampleSource) \
        .join(SampleSource.projects) \
        .join(Groups) \
        .join(Extraction, isouter=True) \
        .filter(Extraction.submitter_plate_id.is_not(None)) \
        .join(TilingPcr, isouter=True) \
        .join(RawSequencing, isouter=True) \
        .join(ReadSet, isouter=True)

    sample = s.query(
            Sample,
            Groups.group_name,
            Groups.institution,
            Project.project_name,
            Sample.sample_identifier,
            Sample.species,
            Sample.sequencing_type_requested,
            Sample.submitter_plate_id,
            Sample.submitter_plate_well,
            Extraction.elution_plate_id,
            Extraction.elution_plate_well,
            Extraction.date_extracted,
            Extraction.extraction_identifier,
            Extraction.nucleic_acid_concentration,
            TilingPcr.date_pcred,
            TilingPcr.pcr_identifier,
            ReadSet.readset_identifier
        ) \
        .filter(Sample.submitter_plate_id.is_not(None)) \
        .join(SampleSource) \
        .join(SampleSource.projects) \
        .join(Groups) \
        .join(Extraction, isouter=True) \
        .join(TilingPcr, isouter=True) \
        .join(RawSequencing, isouter=True) \
        .join(ReadSet, isouter=True)

    # print(sample_culture_extract.all())
    # print(sample_extract.all())
    # print('\t'.join(map(str, sample.all())))
    # print(sample.all()[0], sep='\t')
    union_of_both = sample_culture_extract.union(sample_extract).union(sample).all()

    header = [
        'group_name', 'institution', 'project_name', 'sample_identifier', 'species',
        'sequencing_type_requested', 'submitter_plate_id', 'submitter_plate_well',
        'elution_plate_id', 'elution_plate_well', 'date_extracted', 'extraction_identifier',
        'nucleic_acid_concentration', 'date_tiling_pcred', 'tiling_pcr_identifier',
        'readset_identifier'
    ]
    print('\t'.join(header))
    for x in union_of_both:
        # check that the header is the same length as each return of the query
        # this is in case we add something to the return, but forget to add it
        # to the header
        # we add 1 to the length of the header return because the first element
        # of x is the sample object, which we don't print

        # replace the Nones with empty strings because want to use the output as
        # the input for a future upload and the Nones will cause problems
        x = ['' if y is None else y for y in x]
        #print(type(x[9]))
        # want to get the date, not the datetime.
        # print(x)
        if not x[11] == '':
            x[11] = x[11].date()
        # TODO - write to an outfile instead of printing to stdout
        assert len(header) + 1 == len(x)
        print('\t'.join([str(y) for y in x[1:]]))
    s.close()


def read_in_sample_info(sample_info: dict, submitted_for_sequencing: bool) -> Sample:
    """
    Read in a sample into a Sample object.

    Args:
        sample_info (dict): a dictionary containing the sample information
        submitted_for_sequencing (bool): True if the sample has been submitted for sequencing
    
    Returns:
        Sample: the sample object
    """
    check_samples(sample_info)
    sample = Sample(sample_identifier=sample_info['sample_identifier'])
    if sample_info['species'] != '':
        sample.species = sample_info['species']
    if sample_info['sample_type']:
        sample.sample_type = sample_info['sample_type']
    if sample_info['sample_source_identifier']:
        sample.sample_source_id = sample_info['sample_source_identifier']
    if sample_info['day_collected']:
        sample.day_collected = sample_info['day_collected']
    if sample_info['month_collected']:
        sample.month_collected = sample_info['month_collected']
    if sample_info['year_collected']:
        sample.year_collected = sample_info['year_collected']
    if sample_info['day_received']:
        sample.day_received = sample_info['day_received']
    if sample_info['month_received']:
        sample.month_received = sample_info['month_received']
    if sample_info['year_received']:
        sample.year_received = sample_info['year_received']
    if sample_info['sequencing_type_requested'] != '':
        sample.sequencing_type_requested = sample_info['sequencing_type_requested'].split(';')
    if submitted_for_sequencing:
        if sample_info['submitter_plate_id'].startswith('SAM'):
            sample.submitter_plate_id = sample_info['submitter_plate_id']
            sample.submitter_plate_well = sample_info['submitter_plate_well']
        # TODO: Determine if this is needed, if not remove it
        # if the submitter_plate_id starts with OUT,
        # then the sample is an externally sequenced sample and has no plate info
        # elif sample_info['submitter_plate_id'].startswith('OUT'):
        #     sample.submitter_plate_id = sample_info['submitter_plate_id']
        #     sample.submitter_plate_well = None
    else:
        sample.submitter_plate_id = None
        sample.submitter_plate_well = None
    return sample


def read_in_sample_source_info(sample_source_info: dict) -> SampleSource:
    """
    Read in a sample source into a SampleSource object.

    Args:
        sample_source_info (dict): a dictionary containing the sample source information

    Returns:
        SampleSource: the sample source object
    """
    # Check sample_source_info required fields are not empty
    check_empty_fields(
        sample_source_info,
        ['sample_source_identifier', 'sample_source_type', 'projects', 'group_name',
        'institution']
    )
    sample_source = SampleSource(
        sample_source_identifier=sample_source_info['sample_source_identifier']
    )
    if sample_source_info['sample_source_type']:
        sample_source.sample_source_type = sample_source_info['sample_source_type']
    if sample_source_info['township']:
        sample_source.location_third_level = sample_source_info['township']
    if sample_source_info['city']:
        sample_source.location_second_level = sample_source_info['city']
    if sample_source_info['country']:
        sample_source.country = sample_source_info['country']
    if sample_source_info['latitude']:
        sample_source.latitude = sample_source_info['latitude']
    if sample_source_info['longitude']:
        sample_source.longitude = sample_source_info['longitude']
    return sample_source


def update_sample(sample: Sample):
    """
    Update a sample in the database.

    Args:
        sample (Sample): the sample object
    """
    sample.submitted_for_sequencing = True
    db.session.commit()


def add_tiling_pcr(tiling_pcr_info: dict):
    """
    Add a tiling pcr to the database.

    Args:
        tiling_pcr_info (dict): a dictionary containing the tiling pcr information
    """
    extraction = get_extraction(tiling_pcr_info)
    if not extraction:
        print(
            f"Adding tiling PCR. No Extraction match for {tiling_pcr_info['sample_identifier']}, "
            f"extracted on {tiling_pcr_info['date_extracted']} for extraction id "
            f"{tiling_pcr_info['extraction_identifier']} need to add that extract and re-run. \n"
            f"Exiting.")
        sys.exit(1)
    tiling_pcr = read_in_tiling_pcr(tiling_pcr_info)
    extraction.tiling_pcrs.append(tiling_pcr)
    db.session.add(tiling_pcr)
    db.session.commit()
    print(
        f"Adding tiling PCR for sample {tiling_pcr_info['sample_identifier']} run on "
        f"{tiling_pcr_info['date_tiling_pcred']} PCR id {tiling_pcr_info['tiling_pcr_identifier']} "
        f"to the database."
    )


def get_tiling_pcr(tiling_pcr_info: dict) -> TilingPcr:
    """
    Get a tiling pcr from the database.

    Args:
        tiling_pcr_info (dict): a dictionary containing the tiling pcr information

    Returns:
        TilingPcr: the tiling pcr object, or False if there is no match
    """
    matching_tiling_pcr = TilingPcr.query \
        .filter_by(
            pcr_identifier=tiling_pcr_info['tiling_pcr_identifier'],
            date_pcred=tiling_pcr_info['date_tiling_pcred']
        ) \
        .join(Extraction) \
        .join(Sample) \
        .filter_by(sample_identifier=tiling_pcr_info['sample_identifier']) \
        .all()
    if len(matching_tiling_pcr) == 1:
        return matching_tiling_pcr[0]
    elif len(matching_tiling_pcr) == 0:
        return False
    else:
        print(
            f"Getting tiling PCR. More than one match for {tiling_pcr_info['sample_identifier']} "
            f"on date {tiling_pcr_info['date_tiling_pcred']} with pcr_identifier "
            f"{tiling_pcr_info['tiling_pcr_identifier']}. \n"
            f"This should not happen, exiting.")
        sys.exit(1)


def read_in_tiling_pcr(tiling_pcr_info: dict) -> TilingPcr:
    """
    Read in a tiling pcr into a TilingPcr object.

    Args:
        tiling_pcr_info (dict): a dictionary containing the tiling pcr information

    Returns:
        TilingPcr: the tiling pcr object
    """
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

# Circular dependancy if in check, so move here
def check_sample_source_associated_with_project(sample_source: dict, sample_source_info: dict):
    """
    This func checks if the sample_source is associated with the project is available in the
    database. If not, it raises a ValueError.

    Args:
        sample_source (dict): The sample_sources available in the db
        sample_source_info (dict): The dictionary of sample_source info to check
    
    Raises:
        ValueError: If the sample_source is not associated with the project in the input file
    """
    # TODO: maybe just get rid of this pathway, and have a different Seqbox_cmd function for
    #       if you want to add a new relationship between an existing sample source and project
    # get the projects from the input file as set
    projects_from_input_file = sample_source_info['projects'].split(';')
    projects_from_input_file = set([x.strip() for x in projects_from_input_file])
    # get the projects from the db for this sample_source
    projects_from_db = set([x.project_name for x in sample_source.projects])
    # are there any sample_source to project relationships in the file which aren't
    # represented in the db?
    new_projects_from_file = projects_from_input_file - projects_from_db
    # if there are any
    if len(new_projects_from_file) > 0:
        # then, for each one
        for project_name in new_projects_from_file:
            print(f"Adding existing sample_source {sample_source_info['sample_source_identifier']} to project "
                  f"{project_name}")
            # query projects, this will only return p[0] is True if the project name already
            # exists for this group otherwise, they need to add the project and re-run.
            p = query_projects(sample_source_info, project_name)
            if p[0]:
                # add it to the projects associated with this sample source
                sample_source.projects.append(p[1])
            else:
                print(f"Checking that sample source is associated with project. "
                      f"Project {project_name} from group {sample_source_info['group_name']} "
                      f"does not exist in the db, you need to add it using the seqbox_cmd.py "
                      f"add_projects function.\nExiting now.")
                sys.exit(1)
    # and update the database.
    db.session.commit()
