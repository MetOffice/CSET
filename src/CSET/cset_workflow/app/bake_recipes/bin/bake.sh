#!/usr/bin/env bash
# Run CSET bake for a recipe file.
set -euo pipefail

# Construct command into array.
cset_command=( cset bake \
    --recipe "$1" \
    --output-dir "${CYLC_WORKFLOW_SHARE_DIR}/web/plots/${CYLC_TASK_CYCLE_POINT}/$(basename "$1" .yaml)" \
    ${COLORBAR_FILE:+"--style-file='${CYLC_WORKFLOW_SHARE_DIR}/style.json'"} \
    ${PLOT_RESOLUTION:+"--plot-resolution=$PLOT_RESOLUTION"} \
    ${SKIP_WRITE:+"--skip-write"} )

# Print command for easy rerunning.
echo "${cset_command[@]}"

# Bake recipe.
exec "${cset_command[@]}"
