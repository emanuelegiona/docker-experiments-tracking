from argparse import ArgumentParser
from typing import Optional, Callable, Dict
import wandb

import yaml
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
import multiprocessing as mp
from time import sleep

# Run wrappers defined here
from experiment_runner import RunWrapperSimple, RunWrapperSweep

# Parsing routines defined here
from parse_functions import metric_dict, logfile_dict, artifact_dict



def perform_sweep(proj_name: str,
                  sweep_config: Dict,
                  metrics_dirpath: str,
                  log_dirpath: Optional[str] = None,
                  artifacts_dirpath: Optional[str] = None,
                  metrics_parse_function: Optional[Callable] = None,
                  metrics_method_args: Optional[Dict] = {},
                  logfile_parse_function: Optional[Callable] = None,
                  logfile_method_args: Optional[Dict] = {},
                  artifacts_parse_function: Optional[Callable] = None,
                  artifacts_method_args: Optional[Dict] = {}
    ) -> None:

    """
    Performs a sweep with the provided configuration.
    """

    # Fetch settings for sweep instances
    meta_sweep_config = {}
    if "sweep-setup" in sweep_config:
        meta_sweep_config = sweep_config["sweep-setup"]
        del sweep_config["sweep-setup"]

    sweep_agents = meta_sweep_config.get("agents", 1)
    runs_per_sweep = meta_sweep_config.get("runs-per-sweep", 1)

    # Initialize sweep
    sweep_id = wandb.sweep(sweep=sweep_config, project=proj_name)

    # Setup parallel sweep workers
    workers = []
    for _ in range(sweep_agents):
        wrapper = RunWrapperSweep(sweep_id=sweep_id,
                                  runs_per_sweep=runs_per_sweep,
                                  metrics_dirpath=metrics_dirpath,
                                  log_dirpath=log_dirpath,
                                  artifacts_dirpath=artifacts_dirpath,
                                  metrics_parse_function=metrics_parse_function,
                                  metrics_method_args=metrics_method_args,
                                  logfile_parse_function=logfile_parse_function,
                                  logfile_method_args=logfile_method_args,
                                  artifacts_parse_function=artifacts_parse_function,
                                  artifacts_method_args=artifacts_method_args)

        worker = mp.Process(target=wrapper.setup_run)
        worker.start()
        workers.append(worker)

        # Only necessary in parallel case
        if sweep_agents > 1:
            # Prevent spawning tasks too quickly (multiple W&B logins --> Error 500)
            sleep(0.5)

    # Wait for all workers to end processing
    for worker in workers:
        worker.join()



def perform_single_experiment(proj_name: str,
                              run_config: Dict,
                              config: Dict,
                              metrics_dirpath: str,
                              log_dirpath: Optional[str] = None,
                              artifacts_dirpath: Optional[str] = None,
                              metrics_parse_function: Optional[Callable] = None,
                              metrics_method_args: Optional[Dict] = {},
                              logfile_parse_function: Optional[Callable] = None,
                              logfile_method_args: Optional[Dict] = {},
                              artifacts_parse_function: Optional[Callable] = None,
                              artifacts_method_args: Optional[Dict] = {}
    ) -> None:

    """
    Performs a single experiment with the provided configuration.
    """

    # Fetch run settings
    group_id = run_config.get("group-by", None)
    runs = run_config.get("num-runs-limit", None)
    starting_run = run_config.get("num-runs-start", None)

    # Safe defaults
    if runs is None:
        runs = 1
    else:
        try:
            runs = int(runs)
        except ValueError:
            runs = 1
    if starting_run is None:
        starting_run = 0
    else:
        try:
            starting_run = int(starting_run)
        except ValueError:
            starting_run = 0

    # Fetch parallelism setting for repeated run instances
    parallel = 1
    if "parallel" in run_config:
        parallel = int(run_config["parallel"])
        del run_config["parallel"]

    # Setup parallel repeated runs
    with mp.Pool(processes=parallel) as worker_pool:
        tasks = []

        # Spawn tasks representing a run each
        for curr_run in range(starting_run, runs):
            if group_id is None or group_id == "auto":
                group_id = f"{wandb.util.generate_id()}"

            curr_config = config
            curr_config["run"] = curr_run

            wrapper = RunWrapperSimple(group_id=group_id,
                                       metrics_dirpath=metrics_dirpath,
                                       log_dirpath=log_dirpath,
                                       artifacts_dirpath=artifacts_dirpath,
                                       metrics_parse_function=metrics_parse_function,
                                       metrics_method_args=metrics_method_args,
                                       logfile_parse_function=logfile_parse_function,
                                       logfile_method_args=logfile_method_args,
                                       artifacts_parse_function=artifacts_parse_function,
                                       artifacts_method_args=artifacts_method_args)

            wrapper.run_config(proj_name=proj_name,
                               config=curr_config)

            # Add tasks until there are available workers, blocking otherwise
            tasks.append(worker_pool.apply_async(wrapper.setup_run))

            # Only necessary in parallel case
            if parallel > 1:
                # Prevent spawning tasks too quickly (multiple W&B logins --> Error 500)
                sleep(0.5)

        # Wait for tasks completion
        tasks = [result.get() for result in tasks]



def main(proj_name: str, metrics_dir: str, logs_dir: Optional[str] = None, artifacts_dir: Optional[str] = None,
         config_path: Optional[str] = None, sweep_path: Optional[str] = None
    ) -> None:

    """
    Executes one or more tracked experiments.
    """

    # Read config.yaml file
    config = {}
    if config_path is not None:
        with open(config_path) as config_file:
            config = yaml.load(config_file, Loader)

    # Check parsing functions before running any experiment
    metric_fn = None
    metric_args = {}
    logfile_fn = None
    logfile_args = {}
    artifact_fn = None
    artifact_args = {}

    if "parsing-setup" in config:
        parsing_conf = config["parsing-setup"]
        if "metrics" in parsing_conf:
            metric_fn = metric_dict.get(parsing_conf["metrics"].get("method", "default"), None)
            metric_args = parsing_conf["metrics"].get("args", {})
        else:
            config["parsing-setup"]["metrics"] = {"args": {}}

        if "logfile" in parsing_conf:
            logfile_fn = logfile_dict.get(parsing_conf["logfile"].get("method", "default"), None)
            logfile_args = parsing_conf["logfile"].get("args", {})
        else:
            config["parsing-setup"]["logfile"] = {"args": {}}

        if "artifacts" in parsing_conf:
            artifact_fn = artifact_dict.get(parsing_conf["artifacts"].get("method", "default"), None)
            artifact_args = parsing_conf["artifacts"].get("args", {})
        else:
            config["parsing-setup"]["artifacts"] = {"args": {}}

        del config["parsing-setup"]

    if metric_fn is None:
        raise NotImplementedError("Metric parsing function not found")
    if logfile_fn is None:
        raise NotImplementedError("Logfile parsing function not found")
    if artifact_fn is None:
        raise NotImplementedError("Artifacts parsing function not found")

    # Sweep case
    if sweep_path is not None:
        sweep_config = {}
        with open(sweep_path) as sweep_file:
            sweep_config = yaml.load(sweep_file, Loader)

        # Perform the sweep using the provided configuration
        perform_sweep(proj_name=proj_name,
                      sweep_config=sweep_config,
                      metrics_dirpath=metrics_dir,
                      log_dirpath=logs_dir,
                      artifacts_dirpath=artifacts_dir,
                      metrics_parse_function=metric_fn,
                      metrics_method_args=metric_args,
                      logfile_parse_function=logfile_fn,
                      logfile_method_args=logfile_args,
                      artifacts_parse_function=artifact_fn,
                      artifacts_method_args=artifact_args)

    # Single experiment case
    else:
        run_config = config.get("run-setup", None)
        if run_config is None:
            run_config = {}
        else:
            del config["run-setup"]

        perform_single_experiment(proj_name=proj_name,
                                  run_config=run_config,
                                  config=config,
                                  metrics_dirpath=metrics_dir,
                                  log_dirpath=logs_dir,
                                  artifacts_dirpath=artifacts_dir,
                                  metrics_parse_function=metric_fn,
                                  metrics_method_args=metric_args,
                                  logfile_parse_function=logfile_fn,
                                  logfile_method_args=logfile_args,
                                  artifacts_parse_function=artifact_fn,
                                  artifacts_method_args=artifact_args)



if __name__ == "__main__":
    parser = ArgumentParser("Tracks metrics from simulation experiments")

    # W&B general setup
    parser.add_argument("proj_name", help="Weights & Biases project name")

    # Paths for metrics, logfile, and artifacts
    parser.add_argument("metrics_dir", help="Path to directory containing metrics files")
    parser.add_argument("--logs_dir", help="Path to directory containing log files")
    parser.add_argument("--artifacts_dir", help="Path to directory containing other artifacts to track")

    # Experiment setup
    parser.add_argument("--config_path", help="Path to experiment configuration file", default=None)
    parser.add_argument("--sweep_path", help="Path to sweep configuration file", default=None)

    args = parser.parse_args()

    main(args.proj_name, args.metrics_dir,
         args.logs_dir if len(args.logs_dir) > 0 else None,
         args.artifacts_dir if len(args.artifacts_dir) > 0 else None,
         args.config_path if(args.config_path is not None and len(args.config_path) > 0) else None,
         args.sweep_path if(args.sweep_path is not None and len(args.sweep_path) > 0) else None)

    exit(0)
