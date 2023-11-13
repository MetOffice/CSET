#! /usr/bin/env python3

"""Run a recipe with the CSET CLI."""

import json
import logging
import os
import subprocess
from pathlib import Path
from uuid import uuid4

import redis
from ruamel.yaml import YAML

logging.basicConfig(level=logging.INFO)

r = redis.Redis().from_url(
    Path(f"{os.getenv('CYLC_WORKFLOW_SHARE_DIR')}/redis_uri")
    .read_text(encoding="utf-8")
    .strip()
)
input_file = (
    Path(
        f"{os.getenv('CYLC_WORKFLOW_SHARE_DIR')}/cycle/{os.getenv('CYLC_TASK_CYCLE_POINT')}/input_path"
    )
    .read_text(encoding="utf-8")
    .strip()
)
output_file = f"{os.getcwd()}/{uuid4()}"

# Takes recipe from CSET_RECIPE environment variable.
subprocess.run(("cset", "-v", "bake", input_file, output_file), check=True)

with YAML(typ="safe", pure=True) as yaml:
    recipe = yaml.load(os.getenv("CSET_RECIPE"))

# TODO: Get actual model here.
source_model = "Model #1"

# TODO: Create actual diagnostic log file.
Path(output_file + ".log").write_text("Not yet implemented.")

# Write plot record json
plot_record = json.dumps(
    {
        "model": source_model,
        "title": recipe["title"],
        "description": recipe["description"],
        "plot_data_location": output_file + ".nc",
        "plot_location": output_file + ".svg",
        "raw_data_path": input_file,
        "diagnostic_log_location": output_file + ".log",
    }
)
r.lpush("plot_records", plot_record)
