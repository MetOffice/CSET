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

"""Tests for run_cset_recipe workflow utility."""

import glob
import shutil

import iris

from CSET._workflow_utils import preprocess


def test_preprocess(monkeypatch):
    """Test preprocess run."""
    preprocess_run = False
    monkeypatch.setenv("CYLC_WORKFLOW_SHARE_DIR", "/data")
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "20250101T0000Z")
    monkeypatch.setenv("MODEL_IDENTIFIER", "1")

    def mock_preprocess_data(data_location: str):
        nonlocal preprocess_run
        preprocess_run = True
        assert data_location == "/data/cycle/20250101T0000Z/data/1"

    monkeypatch.setattr(preprocess, "preprocess_data", mock_preprocess_data)
    preprocess.run()
    assert preprocess_run


def test_preprocess_data(tmp_path):
    """Combine model files into one."""
    # Prepare some model data in the data_location.
    for file in glob.glob("tests/test_data/long_forecast_air_temp_fcst_*.nc"):
        shutil.copy(file, tmp_path)

    # Preprocess data.
    preprocess.preprocess_data(str(tmp_path))

    # Check file has been created.
    output = tmp_path / "forecast.nc"
    assert output.is_file()

    # Check cubes have been transferred correctly. We use iris here to avoid
    # re-processing the data.
    cubes = iris.load(output)
    assert len(cubes) == 4
    for cube in cubes:
        assert "cset_comparison_base" not in cube.attributes
