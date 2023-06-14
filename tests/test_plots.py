# Copyright 2022 Met Office and contributors.
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

from pathlib import Path
from uuid import uuid4
import tempfile
import CSET.operators._internal as internal
import logging

logging.basicConfig(level=logging.DEBUG)


def test_spacial_plot():
    """Plot spacial contour plot of instant air temp."""
    input_file = Path("tests/test_data/air_temp.nc")
    output_file = Path(f"{tempfile.gettempdir()}/{uuid4()}")
    recipe_file = Path("tests/test_data/plot_instant_air_temp.yaml")
    internal.execute_recipe(recipe_file, input_file, output_file)
    actual_output_file = output_file.with_suffix(".svg")
    assert actual_output_file.exists()
    actual_output_file.unlink()
