from typing import Dict
import wandb
from os import listdir
from os.path import exists, isfile, join
import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader

# Metrics types define here
from experiment_metrics import metric_type_handling



def default_parse_metrics(wandb_run, metrics_dirpath: str, method_args: Dict = {}, last_file: bool = True) -> None:

    """
    Parses metrics files according to pre-defined metric types, pushing each 
    entry point to Weights & Biases with the specified interpretation.

    If 'last_file' is True: aggregates all metrics with the same name and 
    pushes the result to Weights & Biases.
    """

    for fname in listdir(metrics_dirpath):
        filepath = join(metrics_dirpath, fname)
        if not isfile(filepath) or not filepath.endswith(".yaml"):
            continue

        with open(filepath) as metrics_file:
            metrics = yaml.load(metrics_file, Loader)
            metric_type = metrics["type"]
            type_handling = metric_type_handling.get(metric_type, None)
            if type_handling is None:
                print(f"WARNING: file '{filepath}' contains unsupported metric type '{metric_type}'; skipping")
                continue

            # Log to Weights & Biases according to (customizable) metrics-specific format
            type_handling(wandb_run, metrics, method_args, last_file)



def default_parse_logfile(wandb_run, log_filepath: str, method_args: Dict = {}) -> None:

    """
    Simply uploads the log file to Weights & Biases.
    """

    if not exists(log_filepath):
        return

    columns = ["Logfile"]

    if not isfile(log_filepath):
        lines = [f"ERROR: Path '{log_filepath}' is not a regular file."]
    else:
        with open(log_filepath) as logfile:
            lines = logfile.readlines()
            wandb.Table.MAX_ROWS = len(lines)

    table = wandb.Table(data=lines, columns=columns)
    wandb_run.log({"logfile": table})



def default_parse_artifacts(wandb_run, artifact_dirpath: str, method_args: Dict = {}) -> None:

    """
    Simply uploads all files within the artifact directory to Weights & Biases.
    """

    art = wandb.Artifact(name="artifacts", type="misc")
    art.add_dir(artifact_dirpath)
    wandb_run.log_artifact(art)



# Parsing function dictionaries used for key-based lookup
# Add any custom functions to this dict
metric_dict = {
    "default": default_parse_metrics
}

logfile_dict = {
    "default": default_parse_logfile
}

artifact_dict = {
    "default": default_parse_artifacts
}
