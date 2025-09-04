#!/usr/bin/env bash
# Setup rose app for baking, then bake.
set -euo pipefail

# Use the appropriate recipes.
optconfkey="$CYLC_TASK_CYCLE_POINT"
if [ -n "${DO_CASE_AGGREGATION-}" ]; then
    RECIPE_DIR=$CYLC_WORKFLOW_SHARE_DIR/cycle/$CYLC_TASK_CYCLE_POINT/aggregation_recipes
    optconfkey="${optconfkey}-aggregation"
else
    RECIPE_DIR=$CYLC_WORKFLOW_SHARE_DIR/cycle/$CYLC_TASK_CYCLE_POINT/recipes
fi
if ! [ -d "$RECIPE_DIR" ]; then
    echo "No recipes to bake in $RECIPE_DIR"
    exit 0
fi
export RECIPE_DIR

# Determine parallelism.
parallelism="$(nproc)"
if [ "$CYLC_TASK_TRY_NUMBER" -gt 1 ]; then
    # This is a retry; enable DEBUG logging and run in serial.
    export LOGLEVEL="DEBUG"
    parallelism=1
fi

# Get filenames without leading directory.
# Portability note: printf is specific to GNU find.
recipes="$(find "$RECIPE_DIR" -iname '*.yaml' -type f -printf '%P ')"
# Count and display number of recipes. (By counting the number of spaces.)
echo "Baking $(echo "$recipes" | tr -dc ' ' | wc -c) recipes..."

# Write rose-bunch optional configuration.
mkdir -p "$CYLC_WORKFLOW_RUN_DIR/app/bake_recipes/opt/"
opt_conf="$CYLC_WORKFLOW_RUN_DIR/app/bake_recipes/opt/rose-app-${optconfkey}.conf"
printf "[bunch]\npool-size=%s\n[bunch-args]\nrecipe_file=%s\n" "$parallelism" "$recipes" > "$opt_conf"
unset opt_conf parallelism recipes

# Run bake_recipes rose app.
exec rose task-run -v --app-key=bake_recipes --opt-conf-key="${optconfkey}"
