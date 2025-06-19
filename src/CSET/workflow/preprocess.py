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


def preprocess_data(data_location: str):
    """Rewrite data into a single file. This also fixes all the metadata."""
    # Load up all the data.
    cubes = read.read_cubes(data_location)

    # Remove added comparison base; we don't know if this is the base model yet.
    for cube in cubes:
        del cube.attributes["cset_comparison_base"]

    # Use iris directly to save uncompressed for faster reading.
    iris.save(cubes, "forecast.nc")

    # Remove raw forecast data.
    shutil.rmtree(data_location)
    os.mkdir(data_location)

    # Move forecast data back into place.
    shutil.move("forecast.nc", data_location + "/forecast.nc")


def run():
    """Run workflow script."""
    data_location = (
        f"{os.environ['CYLC_WORKFLOW_SHARE_DIR']}/cycle/"
        f"{os.environ['CYLC_TASK_CYCLE_POINT']}/data/"
        f"{os.environ['MODEL_IDENTIFIER']}"
    )
    print(f"Preprocessing {data_location}")
    preprocess_data(data_location)
