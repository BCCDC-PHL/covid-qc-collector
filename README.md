# covid-qc-collector
Collect QC data from COVID-19 genomic analyses, for loading into the [BCCDC-PHL/covid-qc](https://github.com/BCCDC-PHL/covid-qc) site.

# Installation

# Usage
Start the tool as follows:

```bash
covid-qc-collector --config config.json
```

See the Configuration section of this document for details on preparing a configuration file.

More detailed logs can be produced by controlling the log level using the `--log-level` flag:

```bash
covid-qc-collector --config config.json --log-level debug
```

# Configuration
This tool takes a single config file, in JSON format, with the following structure:

```json
{
  "sequencer_output_dirs": [
    "/path/to/sequencer-01/output"
  ],
  "fastq_input_dir": "/path/to/fastq_input_by_run",
  "analysis_output_dir": "/path/to/analysis_by_run",
  "excluded_runs_list": "/path/to/excluded_runs.csv",
  "output_dir": "/path/to/output",
  "scan_interval_seconds": 3600
}
```

# Logging
This tool outputs [structured logs](https://www.honeycomb.io/blog/structured-logging-and-your-team/) in [JSON Lines](https://jsonlines.org/) format:

Every log line should include the fields:

- `timestamp`
- `level`
- `module`
- `function_name`
- `line_num`
- `message`

...and the contents of the `message` key will be a JSON object that includes at `event_type`. The remaining keys inside the `message` will vary by event type.

```json
{"timestamp": "2022-09-22T11:32:52.287", "level": "INFO", "module", "core", "function_name": "scan", "line_num", 56, "message": {"event_type": "scan_start"}}
```
