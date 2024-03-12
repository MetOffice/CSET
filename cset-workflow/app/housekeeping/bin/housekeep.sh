#! /bin/bash
set -euo pipefail

# Removes intermediatory files to free up disk space. How thoroughly they are
# removed is configurable in rose edit.

if [[ $HOUSEKEEPING_MODE -lt 0 ]]
then
    >&2 echo 'Invalid HOUSEKEEPING_MODE'
    exit 1
elif [[ $HOUSEKEEPING_MODE -eq 0 ]]
then
    # Housekeeping: None
    echo 'Housekeeping is currently disabled.'
elif [[ $HOUSEKEEPING_MODE -eq 1 ]]
then
    # Housekeeping: Debug
    echo 'Removing raw data.'
    rm -rv -- "$CYLC_WORKFLOW_SHARE_DIR/cycle/$CYLC_TASK_CYCLE_POINT"/data || true
elif [[ $HOUSEKEEPING_MODE -ge 2 ]]
then
    # Housekeeping: Standard
    echo 'Removing intermediate data.'
    # Ignore non-zero exit code for next line, as that mean the raw data has
    # already been housekept.
    rm -rv -- "$CYLC_WORKFLOW_SHARE_DIR/cycle/$CYLC_TASK_CYCLE_POINT"/data || true
    rm -rv -- "$CYLC_WORKFLOW_SHARE_DIR"/plot/*/intermediate || true
    rmdir -- "$CYLC_WORKFLOW_SHARE_DIR"/plot/*/intermediate || true
fi
