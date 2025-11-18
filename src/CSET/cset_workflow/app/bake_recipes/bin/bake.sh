#!/usr/bin/env bash
# Run CSET bake for a recipe file.
set -euo pipefail

# Put together path to output dir from nice name for recipe.
output_dir="${CYLC_WORKFLOW_SHARE_DIR}/web/plots/${CYLC_TASK_CYCLE_POINT}/$(basename "$1" .yaml)"

set -x
# Bake recipe.
exec cset bake \
    --recipe "$1" \
    --output-dir "$output_dir" \
    ${COLORBAR_FILE:+"--style-file='${CYLC_WORKFLOW_SHARE_DIR}/style.json'"} \
    ${PLOT_RESOLUTION:+"--plot-resolution=$PLOT_RESOLUTION"} \
    ${SKIP_WRITE:+"--skip-write"}
