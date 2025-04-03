#!/bin/bash

yum install wget -y

wget -qO- https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="$ROOT_DIR/bin:$PATH"
export MAMBA_ROOT_PREFIX="$ROOT_DIR/micromamba"

# Initialize Micromamba shell
"$ROOT_DIR/bin/micromamba" shell init -s bash --no-modify-profile -p $MAMBA_ROOT_PREFIX

# Source Micromamba environment directly
eval "$("$ROOT_DIR/bin/micromamba" shell hook -s bash)"

# Activate the Micromamba environment
micromamba create -n jupyterenv python=3.11 -c conda-forge -y
micromamba activate jupyterenv

# install the dependencies
echo "Using Python: $(which python)"
python --version
python -m pip install -r requirements.txt

# build the JupyterLite site
jupyter lite --version
jupyter lite build --contents content --output-dir dist