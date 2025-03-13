#!/usr/bin/env python3

"""Preprocess forecast data into a single file per model."""

import os
import shutil

import iris

from CSET.operators import read

data_location = (
    f"{os.environ['CYLC_WORKFLOW_SHARE_DIR']}/cycle/"
    f"{os.environ['CYLC_TASK_CYCLE_POINT']}/data/"
    f"{os.environ['MODEL_IDENTIFIER']}"
)
print(f"Preprocessing {data_location}")

# Rewrite data into a single file. This also fixes all the metadata.
cubes = read.read_cubes(data_location)

# Remove added comparison base, as we don't know if this is the base model yet.
for cube in cubes:
    del cube.attributes["cset_comparison_base"]

# We use iris directly here as we want to save uncompressed for faster reading.
iris.save(cubes, "forecast.nc")

# Remove raw forecast data.
shutil.rmtree(data_location)
os.mkdir(data_location)

# Move forecast data back into place.
shutil.move("forecast.nc", data_location + "/forecast.nc")
