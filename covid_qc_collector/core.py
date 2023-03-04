import json
import logging
import os
import re

from typing import Iterator, Optional


def find_analysis_dirs(config, check_complete=True):
    """
    """
    miseq_run_id_regex = "\d{6}_M\d{5}_\d+_\d{9}-[A-Z0-9]{5}"
    nextseq_run_id_regex = "\d{6}_VH\d{5}_\d+_[A-Z0-9]{9}"
    analysis_by_run_dir = config['analysis_by_run_dir']
    subdirs = os.scandir(analysis_by_run_dir)
    
    for subdir in subdirs:
        run_id = subdir.name
        matches_miseq_regex = re.match(miseq_run_id_regex, run_id)
        matches_nextseq_regex = re.match(nextseq_run_id_regex, run_id)
        if check_complete:
            ready_to_collect = True
            # ready_to_collect = os.path.exists()
        else:
            ready_to_collect = True
        
        conditions_checked = {
            "is_directory": subdir.is_dir(),
            "matches_illumina_run_id_format": ((matches_miseq_regex is not None) or (matches_nextseq_regex is not None)),
            "ready_to_collect": ready_to_collect,
        }
        conditions_met = list(conditions_checked.values())

        analysis_directory_path = os.path.abspath(subdir.path)
        analysis_dir = {
            "analysis_directory_path": analysis_directory_path,
        }
        if all(conditions_met):
            logging.info(json.dumps({"event_type": "analysis_directory_found", "sequencing_run_id": run_id, "analysis_directory_path": analysis_directory_path}))
            
            yield analysis_dir
        else:
            logging.debug(json.dumps({"event_type": "directory_skipped", "analysis_directory_path": os.path.abspath(subdir.path), "conditions_checked": conditions_checked}))
            yield None


def scan(config: dict[str, object]) -> Iterator[Optional[dict[str, str]]]:
    """
    Scanning involves looking for all existing runs and...

    :param config: Application config.
    :type config: dict[str, object]
    :return: A run directory to analyze, or None
    :rtype: Iterator[Optional[dict[str, object]]]
    """
    logging.info(json.dumps({"event_type": "scan_start"}))
    for analysis_dir in find_analysis_dirs(config):    
        yield analysis_dir


def collect_outputs(config: dict[str, object], analysis_dir: Optional[dict[str, str]]):
    """
    

    :param config: Application config.
    :type config: dict[str, object]
    :return: 
    :rtype: 
    """
    logging.info(json.dumps({"event_type": "collect_outputs_start"}))

    logging.info(json.dumps({"event_type": "collect_outputs_complete"}))
