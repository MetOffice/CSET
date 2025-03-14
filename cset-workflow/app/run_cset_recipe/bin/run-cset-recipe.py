#! /usr/bin/env python3

"""Run a recipe with the CSET CLI."""

import subprocess

import CSET._workflow_utils.run_cset_recipe

# Tracing process to identify why a node is being slow.
p = subprocess.Popen(
    'sleep 300 && echo "Job on $(hostname) is being slow." && ps -eF', shell=True
)

CSET._workflow_utils.run_cset_recipe.run()

# Kill tracing process if job isn't slow.
p.terminate()
