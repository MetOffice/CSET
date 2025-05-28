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

import os
import shutil

import iris

from CSET.operators import read


def preprocess_data(
    data_location: str | str,
    fields: iris.Constraint | None = None,
    constraints: list | None = None,
):
    """Rewrite data into a single file. This also fixes all the metadata."""
    # Specify variable lists, if required, else read all data
    if fields:
        var_constraint = fields
    else:
        var_constraint = None

    # Load up all the data.
    cubes = read.read_cubes(data_location, constraint=var_constraint)

    # Remove added comparison base; we don't know if this is the base model yet.
    for cube in cubes:
        del cube.attributes["cset_comparison_base"]

    # Remove time0 diagnostics; LFRic does not output T0 so can cause issues.
    ## Option to add this as a time constraint based on value of user-defined
    ## m*_analysis_offset. For initial implementation assume to remove time0.
    cubes = read._remove_time0(cubes)

    # Use iris directly to save uncompressed for faster reading.
    iris.save(cubes, "forecast.nc")

    # Remove raw forecast data.
    shutil.rmtree(data_location)
    os.mkdir(data_location)

    # Move forecast data back into place.
    shutil.move("forecast.nc", data_location + "/forecastB.nc")


def run():
    """Run workflow script."""
    data_location = (
        f"{os.environ['CYLC_WORKFLOW_SHARE_DIR']}/cycle/"
        f"{os.environ['CYLC_TASK_CYCLE_POINT']}/data/"
        f"{os.environ['MODEL_IDENTIFIER']}"
    )
    print(f"Preprocessing {data_location}")

    # Preprocess for only selected variables, else read all
    str_fields = f"{os.environ['FIELDS']}"

    # Parse FIELDS env variable string to list of iris-ready constraint names
    fields = list(
        str_fields.replace("[", "")
        .replace("]", "")
        .replace("'", "")
        .replace(" ", "")
        .split(",")
    )
    if len(fields) > 0:
        print(f"Preprocessing variable list {fields}")
    else:
        fields = None
        print("Preprocessing all variables in files")

    constraints = None

    preprocess_data(data_location, fields=fields, constraints=constraints)
