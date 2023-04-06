from typing import Dict
import wandb
import numpy as np



def network_size(wandb_run, metrics: Dict, method_args: Dict = {}, last_file: bool = True) -> None:

    """
    Handles metrics based on network size steps. 

    Standard W&B Charts are produced for the metric at each network size 
    (e.g. PDR @ 50 nodes, PDR @ 100 nodes, etc.). 
    Optionally, a custom W&B Chart based on a lineseries can be produced 
    (e.g. X-axis being network size, Y-axis being PDR values, using the 
    run group ID as line key).

    If 'last_file' is True: aggregates all metrics with the same name and 
    pushes the result to Weights & Biases.
    """

    # Store metrics for later aggregation
    if not hasattr(network_size, "metrics_storage"):
        network_size.metrics_storage = {}

    metric_name = metrics["metric-name"]
    if metric_name not in network_size.metrics_storage:
        network_size.metrics_storage[metric_name] = []
    network_size.metrics_storage[metric_name].append(metrics)

    # If we have not reached the last file, do not proceed with logging
    if not last_file:
        return

    # Last file reached: aggregate stored metrics and log to W&B
    metrics_list = network_size.metrics_storage.get(metric_name, None)
    if metrics_list is None:
        return
    else:
        del network_size.metrics_storage[metric_name]

    metrics_aggregate = {}
    for m in metrics_list:
        for (x,y) in zip(m["x-values"], m["y-values"]):
            if x not in metrics_aggregate:
                metrics_aggregate[x] = []

            metrics_aggregate[x].append(float(y))

    for (k,v) in metrics_aggregate.items():
        arr = np.array(v)
        v_mean = np.mean(arr)
        metrics_aggregate[k] = v_mean

    # Standard W&B Charts (metrics @ network size and metrics avg across size)
    avg_across_size = [0, 0]
    x_values, y_values = [], []
    for (x,y) in metrics_aggregate.items():
        wandb_run.log({f"{metric_name}_at_{x}": float(y)}, commit=False)
        avg_across_size[0] += float(y)
        avg_across_size[1] += 1
        x_values.append(x)
        y_values.append(y)

    # Useful as W&B Sweep target
    metrics_avg = avg_across_size[0] / avg_across_size[1]
    wandb_run.log({f"{metric_name}_avg": metrics_avg}, commit=True)

    # Custom W&B Chart (line series), if required
    if "lineseries" in method_args and method_args["lineseries"] is True:
        wandb_run.log({f"{metric_name}_series": wandb.plot.line_series(xs=x_values,
                                                                       ys=[y_values],
                                                                       keys=[f"{wandb_run.group}"],
                                                                       title=metrics["y-axis"],
                                                                       xname=metrics["x-axis"])})



# Metrics dictionaries used for key-based lookup
# Add any custom metric to this dict
metric_type_handling = {
    "network-size": network_size
}
