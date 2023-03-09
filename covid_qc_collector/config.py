import json


def get_excluded_runs(config):
    """
    """
    excluded_runs = set()
    with open(config['excluded_runs_list'], 'r') as f:
        for line in f.readlines():
            if not line.startswith('#'):
                run_id = line.strip()
                excluded_runs.add(run_id)

    return excluded_runs


def load_config(config_path: str) -> dict[str, object]:
    """
    """
    with open(config_path, 'r') as f:
        config = json.load(f)

    if 'excluded_runs_list' in config:
        excluded_runs = get_excluded_runs(config)
        config['excluded_runs'] = excluded_runs
    else:
        config['excluded_runs'] = set()

    return config
