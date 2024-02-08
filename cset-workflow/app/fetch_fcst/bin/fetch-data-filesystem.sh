#! /bin/bash

set -euo pipefail
IFS="$(printf '\n\t')"

cycle_share_data_dir="${CYLC_WORKFLOW_SHARE_DIR}/cycle/${CYLC_TASK_CYCLE_POINT}/data"
mkdir -p "$cycle_share_data_dir"

# Pull data from file system. This allows $FILE_PATH to glob.
# shellcheck disable=SC2086
cp -v $FILE_PATH "$cycle_share_data_dir"
