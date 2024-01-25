import json
import csv


def get_excluded_runs(config):
    """
    Get the list of runs to exclude from the config file.

    :param config: The config dictionary
    :type config: dict
    :return: The list of runs to exclude
    :rtype: set[str]
    """
    excluded_runs = set()
    with open(config['excluded_runs_list'], 'r') as f:
        for line in f.readlines():
            if not line.startswith('#'):
                run_id = line.strip()
                excluded_runs.add(run_id)

    return excluded_runs


def get_csv_encoding(file_path, delimiter=','):
    """
    Get the encoding of a file. Try to read the file as utf-8, and if that fails, try iso-8859-1.
    This is necessary to reliably open csv files that may have been created on Windows/Excel.

    :param file_path: The path to the file
    :type file_path: str
    :return: The encoding of the file
    :rtype: str
    """
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f, delimiter=delimiter)
            next(reader)
        return 'utf-8'
    except UnicodeDecodeError:
        return 'iso-8859-1'


def get_failed_plates(config):
    """
    Get the list of failed plates from the config file.

    :param config: The config dictionary
    :type config: dict
    :return: The list of failed plates
    :rtype: set[str]
    """
    failed_plates_by_run = {}
    encoding = get_csv_encoding(config['plate_qc_log'], delimiter=',')
    with open(config['plate_qc_log'], 'r', encoding=encoding) as f:
        reader = csv.DictReader(f, delimiter=',')
    
        for row in reader:
            sequencing_run_id = row['sequencing_run_id']
            plate_id = row['removed_plate_id']
            if sequencing_run_id not in failed_plates_by_run:
                failed_plates_by_run[sequencing_run_id] = set()
            failed_plates_by_run[sequencing_run_id].add(plate_id)

    return failed_plates_by_run


def load_config(config_path: str) -> dict[str, object]:
    """
    Load the config file.

    :param config_path: The path to the config file
    :type config_path: str
    :return: The config dictionary
    :rtype: dict
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    if 'excluded_runs_list' in config:
        excluded_runs = get_excluded_runs(config)
        config['excluded_runs'] = excluded_runs
    else:
        config['excluded_runs'] = set()

    if 'plate_qc_log' in config:
        failed_plates_by_run = get_failed_plates(config)
        config['failed_plates_by_run'] = failed_plates_by_run
    else:
        config['failed_plates_by_run'] = {}
    
    return config
