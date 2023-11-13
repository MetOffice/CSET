#! /bin/bash
set -euxo pipefail

if [[ $HOUSEKEEPING_MODE -gt 1 ]]; then
    # rm -rv "$CYLC_WORKFLOW_SHARE_DIR/cycle/$CYLC_TASK_CYCLE_POINT"/data/*
    true
fi

echo Housekeeping is currently a noop.
