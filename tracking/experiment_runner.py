from typing import Optional, Callable, Dict, List
import subprocess
import wandb
from os import makedirs
from os.path import expandvars, join
import time
import numpy as np



def run_single_experiment(
        config: Dict,
        metrics_dirpath: str,
        log_filepath: Optional[str] = None,
        artifacts_dirpath: Optional[str] = None,
        out_of_config: Dict = {}
    ) -> float:

    """
    Runs a single instance of the experiment specified by the EXPERIMENT_SCRIPT 
    environment variable, passing arguments stored in another environment variable 
    EXPERIMENT_ARGS as well as optional run-specific ones.

    Once the single run has ended, metrics, log file and artifacts are parsed in a 
    standardized way by default, but custom routines may be provided via the method
    'run_parse_functions'.

    Returns: experiment duration time (in seconds)
    """

    # Experiment args setup
    cmd = ["bash", expandvars("$EXPERIMENT_SCRIPT")]

    # First 3 arguments are metrics dir, logfile path, and artifacts dir (if any)
    cmd.append(metrics_dirpath)
    if log_filepath is not None:
        cmd.append(log_filepath)
    if artifacts_dirpath is not None:
        cmd.append(artifacts_dirpath)

    # Rest of the arguments passed: static experiment args and run-specific args
    cmd.append(expandvars("$EXP_ARGS"))

    for (k,v) in config.items():
        cmd.append(f"--{k}={v}")

    for (k,v) in out_of_config.items():
        cmd.append(f"--{k}={v}")

    # Experiment launch
    start = time.perf_counter()
    subprocess.run(cmd)
    end = time.perf_counter()

    return end - start



def run_parse_functions(wandb_run,
                        metrics_dirlist: List[str],
                        logs_pathlist: List[str],
                        artifacts_dirlist: List[str],
                        metrics_parse_function: Optional[Callable] = None,
                        metrics_method_args: Optional[Dict] = {},
                        logfile_parse_function: Optional[Callable] = None,
                        logfile_method_args: Optional[Dict] = {},
                        artifacts_parse_function: Optional[Callable] = None,
                        artifacts_method_args: Optional[Dict] = {}
    ) -> None:

    """
    Parses metrics files, log files, and artifacts at the end of a group of 
    runs, possibly aggregating them.
    """

    # Parse output files
    if metrics_parse_function is not None:
        for i, metrics_dirpath in enumerate(metrics_dirlist):
            metrics_parse_function(wandb_run, metrics_dirpath, metrics_method_args, (i == len(metrics_dirlist) - 1))

    if logfile_parse_function is not None:
        for log_filepath in logs_pathlist:
            logfile_parse_function(wandb_run, log_filepath, logfile_method_args)

    if artifacts_parse_function is not None:
        for artifacts_dirpath in artifacts_dirlist:
            artifacts_parse_function(wandb_run, artifacts_dirpath, artifacts_method_args)



class RunWrapperBase:

    """
    Wrapper class for invoking run_single_experiment() in parallel runs.
    """

    def __init__(self,
                 group_id: str,
                 metrics_dirpath: str,
                 log_dirpath: Optional[str],
                 artifacts_dirpath: Optional[str],
                 metrics_parse_function: Optional[Callable],
                 metrics_method_args: Optional[Dict],
                 logfile_parse_function: Optional[Callable],
                 logfile_method_args: Optional[Dict],
                 artifacts_parse_function: Optional[Callable],
                 artifacts_method_args: Optional[Dict]
        ) -> None:

        """
        Base constructor holding paths to directories, parsing functions and their arguments.
        """

        self.wandb_run = None
        self._group_id = group_id
        self._metrics_dirpath = metrics_dirpath
        self._log_dirpath = log_dirpath
        self._artifacts_dirpath = artifacts_dirpath
        self._metrics_fn = metrics_parse_function
        self._metrics_args = metrics_method_args
        self._logfile_fn = logfile_parse_function
        self._logfile_args = logfile_method_args
        self._artifacts_fn = artifacts_parse_function
        self._artifacts_args = artifacts_method_args

    def setup_run(self) -> None:

        """
        Entry point for a process. Must be implemented by child classes.
        """

        raise NotImplementedError("Must be implemented by a child class")

    def create_run(self) -> None:
        
        """
        Create a run and configures it. Must be implemented by child classes.
        """

        raise NotImplementedError("Must be implemented by a child class")

    def _do_run_experiment(self) -> None:

        """
        Actual invocation of run_single_experiment() with arguments stored upon object creation.
        """

        # Create run based on child class policy
        self.create_run()

        # Create run-specific directories for metrics, logfile, and artifacts
        dir_prefix = f"{self._group_id}"
        curr_metrics_dir = join(self._metrics_dirpath, f"{dir_prefix}_run_{self.wandb_run.id}")
        makedirs(curr_metrics_dir)
        curr_logfile = None
        if self._log_dirpath is not None:
            curr_logfile = join(self._log_dirpath, f"{dir_prefix}_run_{self.wandb_run.id}.log")
        curr_artifacts_dir = None
        if self._artifacts_dirpath is not None:
            curr_artifacts_dir = join(self._artifacts_dirpath, f"{dir_prefix}_run_{self.wandb_run.id}")
            makedirs(curr_artifacts_dir)

        # Actually run the experiment
        duration = run_single_experiment(config=self.wandb_run.config,
                                         metrics_dirpath=curr_metrics_dir,
                                         log_filepath=curr_logfile,
                                         artifacts_dirpath=curr_artifacts_dir)

        # Prepare lists for parse functions and run them
        metrics_dirs = [curr_metrics_dir]
        log_files = []
        if curr_logfile is not None:
            log_files.append(curr_logfile)
        artifacts_dirs = []
        if curr_artifacts_dir is not None:
            artifacts_dirs.append(curr_artifacts_dir)

        run_parse_functions(wandb_run=self.wandb_run,
                            metrics_dirlist=metrics_dirs,
                            logs_pathlist=log_files,
                            artifacts_dirlist=artifacts_dirs,
                            metrics_parse_function=self._metrics_fn,
                            metrics_method_args=self._metrics_args,
                            logfile_parse_function=self._logfile_fn,
                            logfile_method_args=self._logfile_args,
                            artifacts_parse_function=self._artifacts_fn,
                            artifacts_method_args=self._artifacts_args)

        # Track single run duration
        self.wandb_run.log({"duration_secs": duration})

        # Finish W&B Run and upload to cloud
        self.wandb_run.finish()



class RunWrapperSimple(RunWrapperBase):

    """
    Wrapper class for simple runs.
    """

    def __init__(self,
                 group_id: str,
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
        Constructor.
        """

        super().__init__(group_id,
                         metrics_dirpath,
                         log_dirpath,
                         artifacts_dirpath,
                         metrics_parse_function,
                         metrics_method_args,
                         logfile_parse_function,
                         logfile_method_args,
                         artifacts_parse_function,
                         artifacts_method_args)

        self._proj_name = None
        self._run_config = {}

    def run_config(self, proj_name: str, config: Dict) -> None:

        """
        Sets the W&B Run configuration to the provided one.
        """

        self._proj_name = proj_name
        self._run_config = config

    def setup_run(self) -> None:

        """
        Entry point for a process.
        """

        # Nothing else is really needed for the simple run
        super()._do_run_experiment()

    def create_run(self) -> None:
        
        """
        Create a run and configures it.
        """

        # Creates a W&B Run with the given config
        self.wandb_run = wandb.init(project=self._proj_name,
                                    group=self._group_id,
                                    config=self._run_config)



class RunWrapperSweep(RunWrapperBase):

    """
    Wrapper class for W&B Sweep runs.
    """

    def __init__(self,
                 sweep_id: str,
                 runs_per_sweep: int,
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
        Constructor.
        """

        super().__init__(sweep_id,
                         metrics_dirpath,
                         log_dirpath,
                         artifacts_dirpath,
                         metrics_parse_function,
                         metrics_method_args,
                         logfile_parse_function,
                         logfile_method_args,
                         artifacts_parse_function,
                         artifacts_method_args)

        self._sweep_agent = None
        self._runs_per_sweep = runs_per_sweep

    def setup_run(self) -> None:

        """
        Entry point for a process.
        """

        # Create a Sweep Agent
        self._sweep_agent = wandb.agent(self._group_id, function=self._do_run_experiment)

    def create_run(self) -> None:

        """
        Create a run and configures it.
        """

        # Creates a W&B Run with config provided by the Sweep agent
        self.wandb_run = wandb.init()

    def _do_run_experiment(self) -> None:

        """
        Executes repeated runs within the same sweep instance, aggregating results.
        """

        # Create run based on child class policy
        self.create_run()

        # Prepare lists for parse functions
        durations, metrics_dirs, log_files, artifacts_dirs = [], [], [], []

        # Execute repeated runs
        for curr_run in range(self._runs_per_sweep):
            # Create run-specific directories for metrics, logfile, and artifacts
            dir_prefix = f"{self._group_id}"
            curr_metrics_dir = join(self._metrics_dirpath, f"{dir_prefix}_run_{self.wandb_run.id}_{curr_run}")
            makedirs(curr_metrics_dir)
            curr_logfile = None
            if self._log_dirpath is not None:
                curr_logfile = join(self._log_dirpath, f"{dir_prefix}_run_{self.wandb_run.id}_{curr_run}.log")
            curr_artifacts_dir = None
            if self._artifacts_dirpath is not None:
                curr_artifacts_dir = join(self._artifacts_dirpath, f"{dir_prefix}_run_{self.wandb_run.id}_{curr_run}")
                makedirs(curr_artifacts_dir)

            # Actually run the experiment (passing the "run" number too)
            duration = run_single_experiment(config=self.wandb_run.config,
                                             metrics_dirpath=curr_metrics_dir,
                                             log_filepath=curr_logfile,
                                             artifacts_dirpath=curr_artifacts_dir,
                                             out_of_config={"run": curr_run})

            # Store everything from runs
            durations.append(duration)
            metrics_dirs.append(curr_metrics_dir)
            if curr_logfile is not None:
                log_files.append(curr_logfile)
            if curr_artifacts_dir is not None:
                artifacts_dirs.append(curr_artifacts_dir)

        # Run parse functions on stored lists
        run_parse_functions(wandb_run=self.wandb_run,
                            metrics_dirlist=metrics_dirs,
                            logs_pathlist=log_files,
                            artifacts_dirlist=artifacts_dirs,
                            metrics_parse_function=self._metrics_fn,
                            metrics_method_args=self._metrics_args,
                            logfile_parse_function=self._logfile_fn,
                            logfile_method_args=self._logfile_args,
                            artifacts_parse_function=self._artifacts_fn,
                            artifacts_method_args=self._artifacts_args)

        # Track average run duration
        durations = np.array(durations)
        duration = np.mean(durations)
        self.wandb_run.log({"duration_secs": duration})

        # Finish W&B Run and upload to cloud
        self.wandb_run.finish()
