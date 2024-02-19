#! /bin/bash
set -euo pipefail

# Removes intermediatory files to free up disk space. How thoroughly they are
# removed is configurable in rose edit.

if [[ $HOUSEKEEPING_MODE -lt 0 ]]
then
    >&2 echo 'Invalid HOUSEKEEPING_MODE'
    exit 1
fi
if [[ $HOUSEKEEPING_MODE -eq 0 ]]
then
    # Housekeeping: None
    echo 'Housekeeping is currently disabled.'
fi
if [[ $HOUSEKEEPING_MODE -ge 1 ]]
then
    # Housekeeping: Debug
    echo 'Removing raw data.'
    rm -rv "$CYLC_WORKFLOW_SHARE_DIR/cycle/$CYLC_TASK_CYCLE_POINT"/data/*
fi
if [[ $HOUSEKEEPING_MODE -ge 2 ]]
then
    # Housekeeping: Standard
    echo 'Removing intermediate data.'
    rm -rv "$CYLC_WORKFLOW_SHARE_DIR"/plot/*/intermediate
fi
