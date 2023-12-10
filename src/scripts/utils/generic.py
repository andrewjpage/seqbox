import csv
import sys
import datetime
import numpy as np
import pandas as pd

from utils.check import check_plate_ids


def convert_to_datetime_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    This func takes in a dataframe & returns a dataframe with cols containing 'date'
    in them properly converted to a datetime obj

    Args:
        df (pd.DataFrame): a pandas dataframe object

    Returns:
        pd.DataFrame: a pandas dataframe object with date columns converted to datetime objects
    """
    # Get columns with date in them & convert them to datetime
    dated_cols = df.filter(like='date').columns
    convert_dict = {dated_col: 'datetime64[ns]' for dated_col in dated_cols}
    return df.astype(convert_dict)


def convert_to_datetime_dict(each_dict: dict) -> dict:
    """
    This func takes in a dict & takes out keys containing 'date' &
    convert their values to a datetime object

    Args:
        each_dict (dict): a dictionary object

    Returns:
        dict: a dictionary object with date keys converted to datetime objects
    """
    dated_entry = [ key for key in each_dict.keys() if 'date' in key]
    for entry in dated_entry:
        if each_dict[entry]:
            each_dict[entry] = datetime.datetime.strptime(each_dict[entry],'%d/%m/%Y')
    return each_dict


def read_in_as_dict(inhandle: str) -> list:
    """
    Read in a csv or excel file and return a list of dictionaries, where each dictionary is a row in the csv file.

    Args:
        inhandle (str): path to the csv or Excel file
    
    Returns:
        list: each row as a dictionary
    """
    # Check file type i.e is it a csv or xls(x)? then proceed to read accordingly
    if inhandle.endswith('.csv'):
        data = read_in_csv(inhandle)
    elif inhandle.endswith('.xlsx') or inhandle.endswith('.xlx'):
        data = read_in_excel(inhandle)
    else:
        print("Invalid file format")
        sys.exit(1)
    # check the number of plate ids, this field (both elution plate and submitter plate) will be quite susceptible to
    # Excel copy down errors (e.g. EXT001, EXT002 where only supposed to be EXT001), so throw a warning if there is
    # more than one id.
    check_plate_ids(data, 'elution_plate_id')
    check_plate_ids(data, 'submitter_plate_id')

    return data


def read_in_csv(inhandle : str) -> list:
    """
    Read in a csv file and return a list of dictionaries, where each dictionary is a row in the csv file.

    Args:
        inhandle (str): path to the csv file

    Returns:
        list: each row as a dictionary
    """
    # since csv.DictReader returns a generator rather than an iterator, need to do this fancy business to
    # pull in everything from a generator into an honest to goodness iterable.
    with open(inhandle, encoding='utf-8-sig') as f:
        info = csv.DictReader(f)
        # info is a list of ordered dicts, so convert each one to
        list_of_lines = []
        for each_dict in info:
            # print(each_dict)
            # delete data from columns with no header, usually just empty fields
            if None in each_dict:
                del each_dict[None]
            elif '' in each_dict:
                del each_dict['']
            
            # composition: replace empty strings with nones & convert date keys values to datetime
            each_dict = convert_to_datetime_dict(replace_with_none(each_dict))

            new_info = {x: each_dict[x] for x in each_dict}
            # print(new_info)
            # sometimes excel saves blank lines, so only take lines where the length of the set of teh values is > 1
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


def read_in_excel(file: str) -> list:
    """
    Read in an excel file and return a list of dictionaries, where each dictionary is a row in the excel file.

    Args:
        file (str): path to the excel file

    Returns:
        list: _description_
    """
    df = pd.read_excel(file)
    df = convert_to_datetime_df(df)

    # convert NaNs/NaT to None
    df.replace({pd.NaT:None,np.nan:None},inplace=True)

    list_of_lines = [df.iloc[i].to_dict() for i in range(len(df))]
    return list_of_lines


def replace_with_none(each_dict: dict) -> dict:
    """
    This func takes in a dict object & replaces the empty string values with None
    
    Args:
        each_dict (dict): a dictionary object
    
    Returns:
        dict: a dictionary object with empty string values replaced with None
    """
    return {k:None if not v else v for k,v in each_dict.items()}
