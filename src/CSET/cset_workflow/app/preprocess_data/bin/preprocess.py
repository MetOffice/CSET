#! /usr/bin/env python3
# © Crown copyright, Met Office (2022-2025) and CSET contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Preprocess forecast data into a single file per model."""

import ast
import os
import shutil
import tempfile

import iris

from CSET.operators import read


def preprocess_data(data_location: str, fields: iris.Constraint | None = None):
    """Rewrite data into a single file. This also fixes all the metadata."""
    # Load up all the data.
    cubes = read.read_cubes(data_location, constraint=fields)

    # Remove added comparison base; we don't know if this is the base model yet.
    for cube in cubes:
        del cube.attributes["cset_comparison_base"]

    # Remove time0 diagnostics; LFRic does not output T0 so can cause issues.
    ## Option to add this as a time constraint based on value of user-defined
    ## m*_analysis_offset. For initial implementation assume to remove all time0.
    cubes = read._remove_time0(cubes)

    # Work around for the current working directory being used during testing.
    temp_output = tempfile.mktemp(
        suffix=".nc", dir=os.getenv("CYLC_TASK_WORK_DIR", tempfile.gettempdir())
    )

    # Use iris directly to save uncompressed for faster reading.
    iris.save(cubes, temp_output)

    # Remove raw forecast data.
    shutil.rmtree(data_location)
    os.mkdir(data_location)

    # Move forecast data back into place.
    shutil.move(temp_output, os.path.join(data_location, "forecast.nc"))


def run():
    """Run workflow script."""
    data_location = (
        f"{os.environ['CYLC_WORKFLOW_SHARE_DIR']}/cycle/"
        f"{os.environ['CYLC_TASK_CYCLE_POINT']}/data/"
        f"{os.environ['MODEL_IDENTIFIER']}"
    )
    print(f"Preprocessing {data_location}")

    # Preprocess only selected variables, else read all
    str_fields = os.environ["FIELDS"]

    # Parse FIELDS workflow environment variable string to
    # unique list of iris-ready constraint names
    fields = set(ast.literal_eval(str_fields))

    if len(fields) > 0:
        print(f"Preprocessing variable list {fields}.")
    else:
        fields = None
        print("Preprocessing all variables in files.")

    preprocess_data(data_location, fields=fields)


if __name__ == "__main__":
    run()
