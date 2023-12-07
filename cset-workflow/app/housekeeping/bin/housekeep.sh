#! /bin/bash
set -euxo pipefail

# Removes intermediatory files to free up disk space. How thoroughly they are
# removed is configurable in rose edit.

if [[ $HOUSEKEEPING_MODE -gt 1 ]]; then
    # rm -rv "$CYLC_WORKFLOW_SHARE_DIR/cycle/$CYLC_TASK_CYCLE_POINT"/data/*
    true
fi

echo Housekeeping is currently a noop.
