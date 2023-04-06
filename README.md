# docker-experiments-tracking

This repository is useful for tracking experiments run within [Docker][docker] containers by leveraging [Weights & Biases][wandb] cloud services.

In particular, this is designed around [ns-3][ns3] simulations carried out via [ns3-woss images][ns3-woss], with the goal of improving tracking and reproducibility of results.

**Key features:**

- Automated experiment execution and tracking

- Configuration based on shell environment variables and YAML files

- Support for repeated experiment runs: increases results' robustness

- Support for hyperparameter search via Weights & Biases Sweep: simplifies finding optimal tuning

- Parallel execution: multi-processing used to execute independent runs or different sweep agents

## Requirements

The following requirements must be satified to correctly take advantage of this tool:

- Internet connection on machines for experiment execution

- Docker CLI w/ Docker Compose plugin

- Weights & Biases account w/ API subscription key

- A ns-3 simulation script to track

## Basic usage

Please use the following procedure for achieving the intended functionality:

1. Clone this repository to your Internet-connected simulation machine of choice and `cd` into the main directory

```
git clone https://github.com/emanuelegiona/docker-experiments-tracking.git
cd docker-experiments-tracking
```

2. Adjust the Docker image to use for your experiment in file [`docker-compose.yml`][docker-compose] (_e.g._ fully replace `egiona/ns3-woss:u18.04-n3.37-w1.12.4`)

3. Grant execution user rights to [`tracking/entry_script.sh`][entry-script] and [`tracking/experiment.sh`][experiment-script] files:

```
chmod +x tracking/*.sh
```

4. Modify the environment variabiles file [`vars.env`][env-file] as desired: 

- `WANDB_API_KEY` must be set to a valid Weights & Biases API key for login purposes

- `PROJ_NAME` must be set to a project name, which will appear within your profile

- _(Optional)_ `EXP_CONFIG_FILE` may be set to a different YAML file; this file contains general configuration as well as single experiment run setup (see next section for more)

- _(Optional)_ `SWEEP_CONFIG_FILE` may be uncommented to run a W&B Sweep and may be set to a different YAML file; this file contains the sweep configuration (see next section for more)

- _(Optional)_ `EXP_ARGS` may be modified to specify static experiment arguments

5. Modify the [`tracking/experiment.sh`][experiment-script] as you desire; this should run the ns-3 simulation script and write metrics files, log file and possible artifacts to the paths defined in [`vars.env`][env-file]

6. Launch Docker Compose and enjoy your experiments tracking!

```
docker compose up
```

**Note**: if you wanted to leave the experiments running and logout from your simulation machine, you could use the following instead:

```
nohup docker compose up &
```

7. _(Optional)_ Remove the container once the experiment has finished

```
docker compose down
```

## Usage details

This tool executes Docker Compose which creates a container from the specified image.
Additionally it mounts the `tracking` directory of this repository as a volume within the container under the path `/home/tracking`.

The user-provided simulation script is expected to:

- write metrics files within the directory specified by `$METRICS_DIRPATH` (`vars.env` file);

- _optionally_ write a log file to the path specified by `$LOGS_DIRPATH` (`vars.env` file);

- _optionally_ produce artifacts within the directory specified by `$ARTIFACTS_DIRPATH` (`vars.env` file).

Python script [`experiment_tracker.py`][exp-tracker] will read metrics files and log each entry using `wandb.log`; log files and each other file produced inside the directory specified by `$ARTIFACTS_DIRPATH` are going to be pushed as artifacts.

## Execution modes

This tool may be used to launch experiments in two execution modes: **single experiment** or **sweep**.

The [`tracking/config.yaml`][conf-yaml] file specifies general Weights & Biases configuration and the single experiment mode setup.

General configuration is specified by the following reserved YAML entries:

```
parsing-setup:
  metrics:
    method:     --> name of the function to use to parse metrics
    args:       --> dictionary of metrics-parsing configuration
  logfile:
    method:     --> name of the function to use to parse logfiles
    args:       --> dictionary of logfile-parsing configuration
  artifacts:
    method:     --> name of the function to use to parse artifacts
    args:       --> dictionary of artifacts-parsing configuration
```

### Single experiment mode

Single experiment configuration is specified by [`tracking/config.yaml`][conf-yaml] file and via the following reserved YAML entries:

```
run-setup:
  group-by:             --> grouping name for repeated runs or "auto"
  num-runs-limit:       --> upper bound for repeated runs
  num-runs-start:       --> lower bound for repeated runs
  parallel:             --> number of processes to execute runs
```

Repeated runs of a single experiment are achieved by iterating in the range `[num-runs-start, num-runs-limit)`, and passing this value via the `--run` parameter.
If a specific name is provided via `group-by`, runs will be considered as a group when logged to Weights & Biases; otherwise, using `"auto"` will generate a different ID for each run.

The rest of YAML keys are directly passed to the experiment script as arguments in the following format:

```
--key1=value1 ... --keyN=valueN
```

### Sweep mode

Sweep configuration is specified by [`tracking/sweep.yaml`][sweep-yaml] file and according to [Weights & Biases guidelines][wandb-sweeps], with the following additional reserved YAML entries:

```
sweep-setup:
  agents:               --> number of parallel sweep agents to run
  runs-per-sweep:       --> number of repeated runs per sweep instance
```

The value of `agents` will be used to spin up that number of W&B sweep agents, each in its own Python process.
The agent will create a sweep instance, with configuration determined by the sweep algorithm in place, and it will execute a number of experiment runs equal to the `runs-per-sweep` value.
Each run will use the same configuration as provided by the sweep instance, only varying the `--run` parameter to the current run number.

**Note:** Repeated runs are not individually pushed to Weights & Biases. Instead, metrics are aggregated across runs and logged as metrics of a single sweep instance. By default, the aggregation method is the arithmetic mean across runs.

**Note:** `random` and `bayes` sweep methods may run indefinitely, validate your configuration accordingly.

## Metrics format

Default metrics parsing operates on metrics exported to YAML files containing a `type` entry.

This repository ships with a pre-defined `network-size` type that is suitable for tracking network performance metrics at varying network sizes.
It accepts files compliant to the following format:

```
---
type: network-size      --> Type for metrics parsing
metric-name:            --> Name of metrics tracked
x-axis:                 --> Name of X axis in a W&B Lineseries plot
y-axis:                 --> Title of Y axis in a W&B Lineseries plot
x-values:               --> List of values for the X axis
  - x1
  - x2
    ...
  - xN
y-values:               --> List of values for the Y axis
  - y1
  - y2
    ...
  - yN
```

This results in pushing to Weights & Biases the following information:

- `<metric-name>_at_xI` with value equal to `yI` (for `I` in `[1, N]`);

- `<metric-name>_avg` with value equal to the arithmetic mean across values in the X axis (useful for W&B Sweep `metric` configuration);

- `<metric-name>_series` as a custom W&B Chart (Lineseries) with the usual performance vs network size shape.

The `<metric-name>_series` output is enabled only if the `args` entry in `metrics` (within `parsing-setup` configuration) contains the `lineseries` key and its value equals `true`, *e.g.*:

```
metrics:
  method: "default"
  args: {lineseries: true}
```

### Custom metrics, logfile, and artifacts handling

Additional methods and arguments interpretations may be provided in the files [`parse_functions.py`][parse-fns] and [`experiment_metrics.py`][exp-metrics].

Users must take care of updating Python dictionaries at the end of the aforementioned files after implementing their own methods, or they will not be able to use their custom handling routines.

**Note:** Custom functions must preserve function signature, otherwise more customization is required.

**Note:** Apart from custom metrics types handling, it is possible to specify custom aggregation methods for repeated runs within a W&B Sweep instance. By default, simple arithmetic mean is performed.

## License

**Copyright (c) 2023 Emanuele Giona**

This repository is distributed under [MIT License][license]. However, software packages, tools, and other external components used may be subject to a different license, and the license chosen for this repository does not necessarily apply to them.



[docker]: https://www.docker.com/
[wandb]: https://wandb.ai/
[ns3]: https://www.nsnam.org/
[ns3-woss]: https://github.com/SENSES-Lab-Sapienza/ns3-woss-docker
[entry-script]: ./tracking/entry_script.sh
[experiment-script]: ./tracking/experiment.sh
[env-file]: vars.env
[docker-compose]: docker-compose.yml
[exp-tracker]: ./tracking/experiment_tracker.py
[conf-yaml]: ./tracking/config.yaml
[sweep-yaml]: ./tracking/sweep.yaml
[wandb-sweeps]: https://docs.wandb.ai/guides/sweeps/define-sweep-configuration
[parse-fns]: ./tracking/parse_functions.py
[exp-metrics]: ./tracking/experiment_metrics.py
[license]: ./LICENSE
