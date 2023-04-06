#!/bin/bash

# W&B setup
. ${NS3_PY_ENV}/bin/activate
pip install wandb
pip install numpy

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

# Create output files & directories
mkdir ${METRICS_DIRPATH}

if [[ $LOGS_DIRPATH ]]; then
    mkdir ${LOGS_DIRPATH}
fi

if [[ $ARTIFACTS_DIRPATH ]]; then
    mkdir ${ARTIFACTS_DIRPATH}
fi

# Run experiment
PY_SCRIPT_ARGS="${PROJ_NAME} ${METRICS_DIRPATH}"

if [[ $LOGS_DIRPATH ]]; then
    PY_SCRIPT_ARGS="${PY_SCRIPT_ARGS} --logs_dir=${LOGS_DIRPATH}"
fi

if [[ $ARTIFACTS_DIRPATH ]]; then
    PY_SCRIPT_ARGS="${PY_SCRIPT_ARGS} --artifacts_dir=${ARTIFACTS_DIRPATH}"
fi

if [[ $EXP_CONFIG_FILE ]]; then
    PY_SCRIPT_ARGS="${PY_SCRIPT_ARGS} --config_path=${EXP_CONFIG_FILE}"
fi

if [[ $SWEEP_CONFIG_FILE ]]; then
    PY_SCRIPT_ARGS="${PY_SCRIPT_ARGS} --sweep_path=${SWEEP_CONFIG_FILE}"
fi

python ${PY_TRACKING_SCRIPT} ${PY_SCRIPT_ARGS}
