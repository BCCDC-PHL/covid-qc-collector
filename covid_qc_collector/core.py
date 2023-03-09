import collections
import glob
import json
import logging
import os
import re
import shutil

from typing import Iterator, Optional

import covid_qc_collector.parsers as parsers
import covid_qc_collector.samplesheet as samplesheet


def create_output_dirs(config):
    """
    """
    base_outdir = config['output_dir']
    output_dirs = [
        base_outdir,
        os.path.join(base_outdir, 'artic-qc'),
        os.path.join(base_outdir, 'ncov-tools-plots', 'depth-by-position'),
        os.path.join(base_outdir, 'ncov-tools-plots', 'depth-heatmap'),
        os.path.join(base_outdir, 'ncov-tools-plots', 'tree-snps'),
        os.path.join(base_outdir, 'ncov-tools-qc-sequencing'),
        os.path.join(base_outdir, 'ncov-tools-summary'),
    ]
    for output_dir in output_dirs:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)    
    

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
        not_excluded = run_id not in config['excluded_runs']
        if check_complete:
            ready_to_collect = True
            # ready_to_collect = os.path.exists()
        else:
            ready_to_collect = True
        
        conditions_checked = {
            "is_directory": subdir.is_dir(),
            "matches_illumina_run_id_format": ((matches_miseq_regex is not None) or (matches_nextseq_regex is not None)),
            "not_excluded": not_excluded,
            "ready_to_collect": ready_to_collect,
        }
        conditions_met = list(conditions_checked.values())

        analysis_directory_path = os.path.abspath(subdir.path)
        analysis_dir = {
            "path": analysis_directory_path,
        }
        if all(conditions_met):
            logging.info(json.dumps({
                "event_type": "analysis_directory_found",
                "sequencing_run_id": run_id,
                "analysis_directory_path": analysis_directory_path
            }))
            
            yield analysis_dir
        else:
            logging.debug(json.dumps({
                "event_type": "directory_skipped",
                "analysis_directory_path": os.path.abspath(subdir.path),
                "conditions_checked": conditions_checked
            }))
            yield None


def get_plate_ids_for_run(run_id, artic_qc_path):
    """
    """
    plate_ids = set()
    run = collections.OrderedDict()
    with open(artic_qc_path, 'r') as f:
        try:
            next(f)
        except StopIteration as e:
            pass
        for line in f:
            library_id = line.strip().split(',')[0]
            if not (re.match('POS', library_id) or re.match('NEG', library_id)):
                plate_id = int(library_id.split('-')[1])
                plate_ids.add(plate_id)

    plate_ids = list(plate_ids)

    return plate_ids

            
def plates_by_run(config):
    """
    """
    logging.info(json.dumps({"event_type": "collect_plates_by_run_start"}))
    plates_by_run = []
    all_analysis_dirs = sorted(list(os.listdir(config['analysis_by_run_dir'])))
    all_run_ids = filter(lambda x: re.match('\d{6}_[VM]', x) != None, all_analysis_dirs)
    for run_id in all_run_ids:
        if run_id in config['excluded_runs']:
            continue
        sequencer_type = None
        if re.match('\d{6}_M\d{5}_', run_id):
            sequencer_type = 'miseq'
        elif re.match('\d{6}_VH\d{5}_', run_id):
            sequencer_type = 'nextseq'
        samplesheet_path = samplesheet.find_samplesheet_for_run(run_id, config['sequencer_output_dirs'])
        if samplesheet_path and sequencer_type:
            logging.info(json.dumps({
                "event_type": "found_samplesheet_file",
                "run_id": run_id,
                "samplesheet_path": samplesheet_path
            }))
            num_covid19_production_samples_in_samplesheet = samplesheet.count_covid19_production_samples_in_samplesheet(samplesheet_path, sequencer_type)
            fastq_input_dir = os.path.join(config['fastq_input_dir'], run_id)
            fastq_input_paths = glob.glob(os.path.join(fastq_input_dir, '*.fastq.gz'))
            fastq_input_paths = list(filter(lambda x: not re.match('Undetermined_R[12].fastq.gz', os.path.basename(x)), fastq_input_paths))
            artic_qc_path = os.path.join(config['analysis_by_run_dir'], run_id, 'ncov2019-artic-nf-v' + config['artic_output_version'] + '-output', run_id + '.qc.csv')
            if os.path.isfile(artic_qc_path):
                plate_ids = get_plate_ids_for_run(run_id, artic_qc_path)
                if plate_ids:
                    run = collections.OrderedDict()
                    run['run_id'] = run_id
                    run['num_fastq_symlink_pairs'] = int(len(fastq_input_paths) / 2)
                    run['num_covid19_production_samples_in_samplesheet'] = num_covid19_production_samples_in_samplesheet
                    run['plate_ids'] = plate_ids
                    plates_by_run.append(run)
        else:
            logging.error(json.dumps({
                "event_type": "failed_to_find_samplesheet_file",
                "run_id": run_id
            }))

    logging.info(json.dumps({
        "event_type": "collect_plates_by_run_complete"
    }))

    return plates_by_run
    

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


def find_latest_artic_output(analysis_dir):
    """
    """
    artic_output_dir_glob = "ncov2019-artic-nf-v*-output"
    artic_output_dirs = glob.glob(os.path.join(analysis_dir, artic_output_dir_glob))
    latest_artic_output_dir = os.path.abspath(artic_output_dirs[-1])

    return latest_artic_output_dir


def find_latest_ncov_tools_output(artic_output_dir):
    """
    """
    ncov_tools_output_dir_glob = "ncov-tools-v*-output"
    ncov_tools_output_dirs = glob.glob(os.path.join(artic_output_dir, ncov_tools_output_dir_glob))
    latest_ncov_tools_output_dir = os.path.abspath(ncov_tools_output_dirs[-1])

    return latest_ncov_tools_output_dir


def get_plate_numbers(ncov_tools_output_path):
    """
    """
    plate_numbers = []
    for plate_path in glob.glob(os.path.join(ncov_tools_output_path, 'by_plate', '*')):
        plate_number = os.path.basename(plate_path)
        plate_numbers.append(plate_number)

    return plate_numbers


def collect_outputs(config: dict[str, object], analysis_dir: Optional[dict[str, str]]):
    """
    

    :param config: Application config.
    :type config: dict[str, object]
    :return: 
    :rtype: 
    """
    logging.info(json.dumps({"event_type": "collect_outputs_start"}))
    run_id = os.path.basename(analysis_dir['path'])

    # artic-qc
    latest_artic_output_path = find_latest_artic_output(analysis_dir['path'])
    artic_qc_src_file = os.path.join(latest_artic_output_path, run_id + '.qc.csv')
    artic_qc_dst_file = os.path.join(config['output_dir'], "artic-qc", run_id + "_qc.json")
    if not os.path.exists(artic_qc_dst_file):
        artic_qc = parsers.parse_artic_qc(artic_qc_src_file, run_id)
        with open(artic_qc_dst_file, 'w') as f:
            json.dump(artic_qc, f, indent=2)
            logging.info(json.dumps({
                "event_type": "write_artic_qc_complete",
                "run_id": run_id,
                "src_file": artic_qc_src_file,
                "dst_file": artic_qc_dst_file
            }))

    # ncov-tools-plots
    latest_ncov_tools_output_path = find_latest_ncov_tools_output(latest_artic_output_path)

    # plate numbers for run
    plate_numbers = get_plate_numbers(latest_ncov_tools_output_path)

    # ncov-tools-plots/depth-by-position
    depth_by_position_outdir = os.path.join(config['output_dir'], 'ncov-tools-plots', 'depth-by-position')
    for plate_number in plate_numbers:
        depth_by_position_src_file = os.path.join(latest_ncov_tools_output_path, 'by_plate', plate_number, 'plots', run_id + '_' + plate_number + '_depth_by_position.pdf')
        depth_by_position_dst_file = os.path.join(depth_by_position_outdir, run_id + '_' + plate_number + '_depth_by_position.pdf')
        if os.path.exists(depth_by_position_src_file) and not os.path.exists(depth_by_position_dst_file):
            shutil.copyfile(depth_by_position_src_file, depth_by_position_dst_file)
            logging.info(json.dumps({
                "event_type": "copy_depth_by_position_file_complete",
                "run_id": run_id,
                "plate_number": plate_number,
                "src_file": depth_by_position_src_file,
                "dst_file": depth_by_position_dst_file
            }))

    # ncov-tools-plots/depth-heatmap
    depth_by_position_outdir = os.path.join(config['output_dir'], 'ncov-tools-plots', 'depth-heatmap')
    for plate_number in plate_numbers:
        depth_heatmap_src_file = os.path.join(latest_ncov_tools_output_path, 'by_plate', plate_number, 'plots', run_id + '_' + plate_number + '_amplicon_coverage_heatmap.pdf')
        depth_heatmap_dst_file = os.path.join(depth_by_position_outdir, run_id + '_' + plate_number + '_amplicon_coverage_heatmap.pdf')
        if os.path.exists(depth_heatmap_src_file) and not os.path.exists(depth_heatmap_dst_file):
            shutil.copyfile(depth_heatmap_src_file, depth_heatmap_dst_file)
            logging.info(json.dumps({
                "event_type": "copy_depth_heatmap_file_complete",
                "run_id": run_id,
                "plate_number": plate_number,
                "src_file": depth_heatmap_src_file,
                "dst_file": depth_heatmap_dst_file
            }))

    # ncov-tools-plots/tree-snps
    tree_snps_outdir = os.path.join(config['output_dir'], 'ncov-tools-plots', 'tree-snps')
    for plate_number in plate_numbers:
        tree_snps_src_file = os.path.join(
            latest_ncov_tools_output_path,
            'by_plate',
            plate_number,
            'plots',
            run_id + '_' + plate_number + '_tree_snps.pdf'
        )
        tree_snps_dst_file = os.path.join(
            tree_snps_outdir,
            run_id + '_' + plate_number + '_tree_snps.pdf'
        )
        if os.path.exists(tree_snps_src_file) and not os.path.exists(tree_snps_dst_file):
            shutil.copyfile(tree_snps_src_file, tree_snps_dst_file)
            logging.info(json.dumps({
                "event_type": "copy_tree_snps_file_complete",
                "run_id": run_id,
                "plate_number": plate_number,
                "src_file": tree_snps_src_file,
                "dst_file": tree_snps_dst_file
            }))

    # ncov-tools-qc-sequencing
    qc_sequencing_outdir = os.path.join(config['output_dir'], 'ncov-tools-qc-sequencing', run_id)
    if not os.path.exists(qc_sequencing_outdir):
        os.makedirs(qc_sequencing_outdir)
    for plate_number in plate_numbers:
        amplicon_depth_files_glob = os.path.join(latest_ncov_tools_output_path, 'by_plate', plate_number, 'qc_sequencing', '*.amplicon_depth.bed')
        for amplicon_depth_src_file in glob.glob(amplicon_depth_files_glob):
            library_id = os.path.basename(amplicon_depth_src_file).split('.')[0]
            amplicon_depth_dst_file = os.path.join(
                qc_sequencing_outdir,
                library_id + '_amplicon_depth.json'
            )
            if not os.path.exists(amplicon_depth_dst_file):
                amplicon_depth = parsers.parse_amplicon_depth_bed(amplicon_depth_src_file)
                with open(amplicon_depth_dst_file, 'w') as f:
                    json.dump(amplicon_depth, f, indent=2)
                    logging.info(json.dumps({"event_type": "amplicon_depth_file_complete", "run_id": run_id, "plate_number": plate_number, "library_id": library_id, "src_file": amplicon_depth_src_file, "dst_file": amplicon_depth_dst_file}))
        
    
    # ncov-tools-qc-summary
    qc_summary_outdir = os.path.join(config['output_dir'], 'ncov-tools-summary')
    for plate_number in plate_numbers:
        summary_qc_src_file = os.path.join(
            latest_ncov_tools_output_path,
            'by_plate',
            plate_number,
            'qc_reports',
            run_id + '_' + plate_number + '_summary_qc.tsv'
        )
        summary_qc_dst_file = os.path.join(
            qc_summary_outdir,
            run_id + '_' + plate_number + '_summary_qc.json'
        )
        if os.path.exists(summary_qc_src_file) and not os.path.exists(summary_qc_dst_file):
            ncov_tools_summary_qc = parsers.parse_ncov_tools_summary_qc(summary_qc_src_file)
            with open(summary_qc_dst_file, 'w') as f:
                json.dump(ncov_tools_summary_qc, f, indent=2)
                logging.info(json.dumps({"event_type": "ncov-tools_summary_qc_file_complete", "run_id": run_id, "plate_number": plate_number, "src_file": summary_qc_src_file, "dst_file": summary_qc_dst_file}))

    logging.info(json.dumps({"event_type": "collect_outputs_complete"}))
