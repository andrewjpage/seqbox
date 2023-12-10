import sys

from app import db
from scripts.utils.db import query_projects

VALID_PLATE_WELLS = {
    'A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9', 'A10', 'A11', 'A12',
    'B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B9', 'B10', 'B11', 'B12',
    'C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9', 'C10', 'C11', 'C12',
    'D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9', 'D10', 'D11', 'D12',
    'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'E10', 'E11', 'E12',
    'F1', 'F2', 'F3', 'F4', 'F5', 'F6', 'F7', 'F8', 'F9', 'F10', 'F11', 'F12',
    'G1', 'G2', 'G3', 'G4', 'G5', 'G6', 'G7', 'G8', 'G9', 'G10', 'G11', 'G12',
    'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11', 'H12',
}


def check_basic_readset_fields(readset_info: dict) -> bool:
    """
    This func checks if the readset_info dict contains all the required fields. This is
    a basic check to not try and make a readset record when it looks like the readset is
    totally missing, which would be the case in the combined input file if the covid
    confirmatory pcr was negative.

    Args:
        readset_info (dict): The dictionary to check

    Returns:
        bool: True if all required fields are present, False otherwise
    """
    to_check = ['data_storage_device', 'readset_batch_name']
    for r in to_check:
        if r not in readset_info or not(readset_info[r]):
            print(f'Warning - {r} column should not be empty. it is for \n{readset_info}.')
            return False
    return True


def check_cultures(culture_info: dict) -> bool:
    """
    This func checks if the culture_info dict contains all the required fields. If culture
    identifier and culture date are not there, then we assume that the sample is not
    cultured and return False.

    Args:
        culture_info (dict): The dictionary to check

    Returns:
        bool: True if culture_identifier and date_cultured,
              False if culture_identifier and date_cultured are both empty
              ValueError is raised if missing culture_identifier or date_cultured
    """
    if (not(culture_info['culture_identifier'])) and (not(culture_info['date_cultured'])):
        print(
            f'No culture information for sample - {culture_info["sample_identifier"]}. ',
            f'Continuing.'
        )
        return False
    elif (culture_info['culture_identifier']) and (culture_info['date_cultured']):
        return True
    else:
        raise ValueError(
            f'date_cultured and culture_identifier column should either both be empty or '
            f'both be filled in. This is not the case for \n{culture_info}\nExiting.'
        )

    # TODO: These checks are after the if/else block, so they were never run
    #       It is not clear if they were needed, if not needed then remove them.
    """
    # we assert that the submitter plate is for cultures
    # or, if the client submitted culture extracts, extraction_from is cultured_isolate
    # or, if the readset was sequenced elsewhere, the submitter_plate_id starts with OUT
    assert culture_info['submitter_plate_id'].startswith('CUL') or \
           culture_info['extraction_from'] == 'cultured_isolate' or \
           culture_info['submitter_plate_id'].startswith('OUT')
    
    # we assert that the submitter plate well is in the allowed values
    assert culture_info['submitter_plate_well'] in VALID_PLATE_WELLS
    """


def check_empty_field(d: dict, key: str):
    """
    This func takes in a value & a key & checks if the value is empty.
    If it is, it raises an error with the key & the value

    Args:
        d (str): Dictionary to check
        key (str): The key of the value

    Raises:
        ValueError: If the value is empty
    """
    if key not in d or not d[key]:
        raise ValueError(
            f'{key} column should not be empty for \n{d}\nExiting.'
        )


def check_empty_fields(d: dict, keys: list):
    """
    This func takes in a value and a key and checks if the value is empty.
    If it is, it raises an error with the key & the value

    Args:
        d (str): Dictionary to check
        keys (list): The keys of the value

    Raises:
        ValueError: If the value is empty
    """
    for key in keys:
        check_empty_field(d, key)


def check_extraction_fields(extraction_info: dict) -> bool:
    """
    This function should:
     1. return True if all extraction fields are present
     2. return False if all fields are blank
     3. ValueError if some extraction fields are not present

    Args:
        extraction_info (dict): The dictionary of extraction info to check

    Returns:
        bool: True if all extraction fields are present, False otherwise
    """
    # Check if the extraction specific columns are blank
    if (('date_extracted' not in extraction_info or not extraction_info['date_extracted']) and
       ('extraction_identifier' not in extraction_info or not extraction_info['extraction_identifier'])):
        # if so, return false
        return False

    # Check individual columns if they are blank
    check_empty_fields(
        extraction_info,
        ['sample_identifier', 'date_extracted', 'group_name', 'extraction_identifier',
        'extraction_from'],
    )

    # Check if the extraction_from column is one of the allowed values
    allowed_extraction_from = ['cultured_isolate', 'whole_sample']
    if extraction_info['extraction_from'] not in allowed_extraction_from:
        raise ValueError(
            f'extraction_from column must be one of {allowed_extraction_from}, '
            f'it is not for \n{extraction_info}\n.'
        )

    # if it's submission of an external dataset (i.e. plate id starts with OUT), then we dont
    # need nucleic_acid_concentration or submitter_plate_well
    if not extraction_info['submitter_plate_id'].startswith('OUT'):
        check_empty_field(extraction_info, 'nucleic_acid_concentration')
        allowed_submitter_plate_well = {**VALID_PLATE_WELLS, **{'N/A'}}
        if extraction_info['submitter_plate_well'] not in allowed_submitter_plate_well:
            raise ValueError(
                f'submitter_plate_well column should be one of {allowed_submitter_plate_well}, '
                f'it is not for \n{extraction_info}\n.'
            )

    # Check if the submitter_plate_id column is one of the allowed prefixes
    allowed_submitter_plate_prefixes = ('EXT', 'CUL', 'SAM', 'OUT')
    if not extraction_info['submitter_plate_id'].startswith(allowed_submitter_plate_prefixes):
        raise ValueError(
            f'submitter_plate_id column should start with one of: {allowed_submitter_plate_prefixes}. '
            f'it does not for \n{extraction_info}\n.'
        )

    # NOTE: There might not be a submitter name for in-house lab extraction from a culture
    return True


def check_invalid_character(character: str, d: dict, key: str):
    """
    This func takes in a character, a value & a key & checks if the value contains
    the character. If it does, it raises an error with the key & the value

    Args:
        character (str): The character to check
        d (str): Dictionary to check
        key (str): The key of the value

    Raises:
        ValueError: If the value contains the character
    """
    if character in d[key]:
        raise ValueError(
            f'{key} column contains invalid character ("{character}")\n{d}\nExiting.'
        )


def check_invalid_characters(characters: list, d: dict, key: str):
    """
    This func takes in a list of invalid characters to check if given value contains.
    If it does, it raises an error with the key & the value

    Args:
        characters (list): The characters to check
        d (str): Dictionary to check
        key (str): The key of the value

    Raises:
        ValueError: If the value contains any of the characters
    """
    for character in characters:
        check_invalid_character(character, d, key)


def check_pangolin_result(pangolin_result_info: dict) -> bool:
    """
    This func checks if the pangolin_result_info dict contains all the required fields

    Args:
        pangolin_result_info (dict): The dictionary of Pangolin results

    Returns:
        bool: True if all required fields are present, False otherwise
    """
    check_empty_fields(
        pangolin_result_info,
        ['taxon', 'lineage', 'status']
    )

    # the name of the output column changed from status to qc_status 2022-07-04
    if 'qc_status' in pangolin_result_info:
        if 'status' not in pangolin_result_info:
            pangolin_result_info['status'] = pangolin_result_info['qc_status']
    return True


def check_pcr_result(pcr_result_info: dict) -> bool:
    """
    This func checks if the pcr_result_info dict contains all the required fields

    Args:
        pcr_result_info (dict): The dictionary of PCR results

    Returns:
        bool: True if all required fields are present, False otherwise
    """
    to_check = ['sample_identifier', 'date_pcred', 'pcr_identifier', 'group_name', 'assay_name']
    for r in to_check:
        if r not in pcr_result_info or not(pcr_result_info[r]):
            print(f'{r} column should not be empty. it is for \n{pcr_result_info}')
            return False

    allowable_results = {
        'Negative', 'Negative - Followup',
        'Positive - Followup', 'Positive',
        'Indeterminate', 'Not Done'
    }
    if pcr_result_info['pcr_result'] not in allowable_results:
        raise ValueError(
            f'pcr_result column should contain one of these results {allowable_results}. '
            f'it does not for \n{pcr_result_info}\nExiting.'
        )
    return True


def check_plate_ids(data: list, plate_id_type: str) -> bool:
    """
    This func checks if the plate_id_type is in the data and if there are multiple
    plate_ids, it raises a warning.

    Args:
        data (list): The list of dictionaries to check
        plate_id_type (str): The plate_id_type to check

    Returns:
        bool: True plate_id_type not in data, or False if it is, and there is only one
    """
    if plate_id_type in data[0]:
        # get the unique ones
        plate_ids = set([x[plate_id_type] for x in data])
        # if there are more than one
        if len(plate_ids) > 1:
            # print a warning
            print(
                f"Warning: multiple {plate_id_type}. Are there supposed to be{plate_ids} "
                f"as {plate_id_type}? Progressing with upload, but if this was an error, "
                f" you need to fix it (e.g. email the bioinformatics team)."
            )
            return False
    return True


def check_readset_fields(
        readset_info: dict, nanopore_default: bool, raw_sequencing_batch: dict, covid: bool
    ) -> bool:
    """
    This func checks if all the required fields for adding a new readset are present

    Args:
        readset_info (dict): The dictionary of readset info to check
        nanopore_default (bool): True if it follows standard Nanopore format
        raw_sequencing_batch (dict): The dictionary of raw_sequencing_batch info
        covid (bool): True if covid, False if not

    Returns:
        bool: True if all required fields are present, False otherwise
    """
    # this is the full check of the readset fields, when it looks like the readset is present.
    check_empty_fields(
        readset_info,
        ['data_storage_device', 'sample_identifier', 'group_name', 'readset_batch_name']
    )

    if raw_sequencing_batch.sequencing_type == 'nanopore':
        if nanopore_default:
            check_empty_field(readset_info, 'barcode')
        else:
            check_empty_fields(readset_info, ['path_fastq', 'path_fast5'])
    # TODO: Determine if this still needed, if not remove it.
    # not taking the read paths from the input file anymore, will get them from the inbox_from_config/batch/sample_name
    # elif raw_sequencing_batch.sequencing_type == 'illumina':
    #     if not readset_info['path_r1']:
    #         print(f'path_r1 column should not be empty. it is for \n{readset_info}\nExiting.')
    #         sys.exit(1)
    #     if not readset_info['path_r2']:
    #         print(f'path_r2 column should not be empty. it is for \n{readset_info}\nExiting.')
    #         sys.exit(1)
    if covid:
        check_empty_fields(
            readset_info,
            ['date_tiling_pcred', 'tiling_pcr_identifier']
        )
    else:
        check_empty_fields(
            readset_info,
            ['date_extracted', 'extraction_identifier']
        )
    return True


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


def check_samples(sample_info: dict) -> bool:
    """
    This func checks if the sample_info dict contains all the required fields

    Args:
        sample_info (dict): The dictionary of sample info to check

    Returns:
        bool: True if all required fields are present, False otherwise
    """
    check_empty_fields(
        sample_info,
        ['sample_identifier', 'sample_source_identifier', 'group_name', 'institution']
    )
    return True


def check_tiling_pcr(tiling_pcr_info: dict) -> bool:
    """
    This func checks if the tiling_pcr_info dict contains all the required fields

    Args:
        tiling_pcr_info (dict): The dictionary of tiling_pcr info to check

    Returns:
        bool: True if all required fields are present, False otherwise
    """
    to_check = [
        'sample_identifier', 'date_extracted', 'extraction_identifier', 'date_tiling_pcred',
        'tiling_pcr_identifier', 'group_name', 'tiling_pcr_protocol'
    ]
    for r in to_check:
        if r not in tiling_pcr_info or not(tiling_pcr_info[r]):
            print(
                f'Warning - {r} column should not be empty. it is for \n{tiling_pcr_info}. '
                'Not adding this tiling pcr record.'
            )
            return False
    return True


def rename_dodgy_mykrobe_variables(mykrobe_result_info: dict) -> dict:
    """
    This func renames the mykrobe variables that may have poorly formatted in the
    original Mykrobe outputs.

    Args:
        mykrobe_result_info (dict): The dictionary of mykrobe results

    Returns:
        dict: The dictionary of mykrobe results with renamed variables
    """
    if 'variants (dna_variant-AA_variant:ref_kmer_count:alt_kmer_count:conf) [use --format json for more info]' in mykrobe_result_info:
        if 'variants' not in mykrobe_result_info:
            mykrobe_result_info['variants'] = mykrobe_result_info['variants (dna_variant-AA_variant:ref_kmer_count:alt_kmer_count:conf) [use --format json for more info]']
    if 'genes (prot_mut-ref_mut:percent_covg:depth) [use --format json for more info]' in mykrobe_result_info:
        if 'genes' not in mykrobe_result_info:
            mykrobe_result_info['genes'] = mykrobe_result_info['genes (prot_mut-ref_mut:percent_covg:depth) [use --format json for more info]']
    return mykrobe_result_info
