#!/bin/bash

# Runs the NCI demo in the currently checked out CSET repository

set -eu
set -o pipefail

SCRIPT_DIR="$( cd -- "$( dirname -- "$(readlink -f "${BASH_SOURCE[0]}")" )" &> /dev/null && pwd )"

# Load the CSET module
module use /g/data/access/ngm/modules
module use /g/data/hr22/modulefiles
module load cylc cset

CSET_DIR=$(readlink -f "$SCRIPT_DIR/../..")
BRANCH_NAME="$(cd $CSET_DIR && git branch --show-current)"
WORK_DIR=$(mktemp --tmpdir -d csetXXXXXX)

# Set up to run from the checked out CSET repository
export PYTHONPATH="$CSET_DIR/src:${PYTHONPATH:-}"

# Check out the workflow
cset extract-workflow "$WORK_DIR"
FLOW_DIR=$(ls -d "$WORK_DIR"/cset-workflow-*)

# Set up rose-suite.conf using the example
ln -s "rose-suite.conf.example" "$FLOW_DIR/rose-suite.conf"

# Put the workflow into cylc-src
mkdir -p "$HOME/cylc-src/cset-demo"
rsync -av --delete "$FLOW_DIR/" "$HOME/cylc-src/cset-demo/$BRANCH_NAME/"

rm -r "$WORK_DIR"

# Run CSET
if [[ -d "$HOME/cylc-run/cset-demo/$BRANCH_NAME" ]]; then
    # Run exists, reload it
    cylc vr "cset-demo/$BRANCH_NAME"
else
    # New run
    cylc vip --no-run-name -O nci-demo -S "CSET_DIR='$CSET_DIR'" "cset-demo/$BRANCH_NAME"
fi
