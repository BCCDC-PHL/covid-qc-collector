import glob
import os
import re


def find_samplesheet_for_run(run_id, sequencer_output_dirs):
    """
    """
    samplesheet_path = None
    
    return samplesheet_path


def count_covid19_production_samples_in_samplesheet(samplesheet_path):
    """
    """
    num_covid19_production_samples = 0
    if re.match('\d{6}_VH', os.path.basename(os.path.dirname(samplesheet_path))):
        with open(samplesheet_path, 'r') as f:
            for row in f:
                if re.search(',covid-19_production,', row):
                    num_covid19_production_samples += 1
    elif re.match('\d{6}_M', os.path.basename(os.path.dirname(samplesheet_path))):
        covid_library_id_regexes = [
            'S\d{1,3},[ER]\d{10},',                                  # Container ID only
            'S\d{1,3},[FHSTW]\d{6},',                                # Foreign Container ID
            'S\d{1,3},X\d{5},',                                      # Foreign Container ID
            'S\d{1,3},[ER]\d{10}-\d{1,4}-[A-Z0-9]{1,2}-[A-H]\d{2},', # Container ID-Plate Num-Index Set ID-Well
            'S\d{1,3},POS',                                          # Positive control
            'S\d{1,3},NEG',                                          # Negative control
        ]
        with open(samplesheet_path, 'r') as f:
            for row in f:
                library_id_matches = []
                for r in covid_library_id_regexes:
                    if re.match(r, row):
                        library_id_matches.append(re.match(r, row).group(0))
                    else:
                        library_id_matches.append(None)
                if any(library_id_matches):
                    num_covid19_production_samples += 1

    return num_covid19_production_samples
