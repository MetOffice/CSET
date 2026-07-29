# © Crown copyright, Met Office (2022-2024) and CSET contributors.
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

"""Tests for module fetch_nimrod.py."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import numpy as np
from iris.cube import Cube

from CSET.cset_workflow.app.fetch_nimrod.bin import fetch_nimrod
from CSET.cset_workflow.app.fetch_nimrod.bin.fetch_nimrod import (
    _get_needed_environment_variables_nimrod,
    apply_radar_weights,
)


def test_apply_radar_weights_leaves_good_values_and_zeroes_bad():
    """Test that Nimrod weights are correctly applied to hourly rainfall accumulations."""
    obs = Cube([[1.0, 2.0], [3.0, 4.0]])
    weights = Cube([[11, 12], [10, 13]])

    obs_out, wei_out = apply_radar_weights(obs, weights)

    assert np.array_equal(wei_out.data, np.array([[11, 12], [10, 13]]))
    assert np.array_equal(obs_out.data, np.array([[1.0, 2.0], [0.0, 4.0]]))


def test_apply_radar_weights_unpack_packed_weights():
    """Test that Nimrod weights are correctly unpacked."""
    obs = Cube([[1.0, 2.0], [3.0, 4.0]])
    packed = Cube([[13 / 32, 12 / 32], [10 / 32, 11 / 32]])

    obs_out, wei_out = apply_radar_weights(obs, packed)

    assert np.array_equal(wei_out.data, np.array([[13, 12], [10, 11]]))
    assert np.array_equal(obs_out.data, np.array([[1.0, 2.0], [0.0, 4.0]]))

    obs = Cube([[1.0, 2.0], [3.0, 4.0]])
    packed = Cube([[13, 12], [10, 11]])

    obs_out, wei_out = apply_radar_weights(obs, packed)

    assert np.array_equal(wei_out.data, np.array([[13, 12], [10, 11]]))
    assert np.array_equal(obs_out.data, np.array([[1.0, 2.0], [0.0, 4.0]]))


# Tests for env loading and parsing logic.
def test_get_needed_environment_variables_nimrod(monkeypatch):
    """Test reading in the environment variables required to fetch Nimrod data."""
    monkeypatch.setenv("NIMROD_COMP_XKM", "True")
    monkeypatch.setenv("NIMROD_COMP_1KM", "False")
    monkeypatch.setenv("NIMROD_COMP_2KM", "False")
    monkeypatch.setenv("NIMROD_COMP_5MIN", "False")
    monkeypatch.setenv("NIMROD_WEIGHTS", "True")
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "2026-05-06T12:00:00")
    monkeypatch.setenv("ANALYSIS_LENGTH", "PT01H")
    monkeypatch.setenv("ROSE_DATAC", "/tmp/rose_datac")

    variables = _get_needed_environment_variables_nimrod()

    assert variables["field"] == ["Nimrod_comp_xkm"]
    assert variables["weights"] == "True"
    assert variables["date_type"] == "initiation"
    assert variables["data_time"] == datetime.fromisoformat("2026-05-06T12:00:00")
    assert variables["forecast_length"].total_seconds() == 3600
    assert variables["rose_datac"] == "/tmp/rose_datac"


def test_retrieve_nimrod_saves_observation_and_weights(tmp_path, monkeypatch):
    """Test retrieve_nimrod saves both observation and weight files when available."""
    # Create a temporary nimrod dictionary file.
    nimrod_dict = {
        "Nimrod_comp_xkm": {
            "obs_id": "nimrod_xkm",
            "wei_id": "nimrod_xkm_weights",
            "basedir": "/data/nimrod",
            "obs_dir": "obs",
            "obs_fname": "_obs.nc",
            "weights_dir": "weights",
            "weights_fname": "_weights.nc",
            "freq": "PT01H",
        }
    }
    config_path = tmp_path / "restricted_nimrod_met_office.json"
    config_path.write_text(json.dumps(nimrod_dict))

    # Set the required environment variables.
    monkeypatch.setenv("NIMROD_COMP_XKM", "True")
    monkeypatch.setenv("NIMROD_COMP_1KM", "False")
    monkeypatch.setenv("NIMROD_COMP_2KM", "False")
    monkeypatch.setenv("NIMROD_COMP_5MIN", "False")
    monkeypatch.setenv("NIMROD_WEIGHTS", "True")
    monkeypatch.setenv("CYLC_TASK_CYCLE_POINT", "2026-05-07T12:00:00")
    monkeypatch.setenv("ANALYSIS_LENGTH", "PT00H")
    rose_datac = tmp_path / "rose_datac"
    monkeypatch.setenv("ROSE_DATAC", str(rose_datac))

    # Point the module at the temporary metadata file.
    monkeypatch.setattr(fetch_nimrod, "nimrod_met_office", str(config_path))

    # Prepare mocked Iris cubes for observation and weights.
    obs_cube = MagicMock()
    weights_cube = MagicMock()
    obs_cube.data = MagicMock()
    weights_cube.data = MagicMock()

    monkeypatch.setattr(
        fetch_nimrod.iris, "load_cube", MagicMock(side_effect=[obs_cube, weights_cube])
    )
    save_calls = []

    def save_side_effect(cube, filename):
        save_calls.append((cube, str(filename)))

    monkeypatch.setattr(
        fetch_nimrod.iris, "save", MagicMock(side_effect=save_side_effect)
    )
    monkeypatch.setattr(fetch_nimrod.os, "makedirs", MagicMock())
    monkeypatch.setattr(
        fetch_nimrod,
        "apply_radar_weights",
        MagicMock(return_value=(obs_cube, weights_cube)),
    )

    fetch_nimrod.retrieve_nimrod()

    assert fetch_nimrod.iris.load_cube.call_count == 2
    assert fetch_nimrod.iris.save.call_count == 2
    fetch_nimrod.apply_radar_weights.assert_called_once_with(obs_cube, weights_cube)

    expected_obs_file = str(
        Path(rose_datac) / "data" / "nimrod_xkm" / "202605071200_nimrod_xkm.nc"
    )
    expected_weight_file = str(
        Path(rose_datac)
        / "data"
        / "nimrod_xkm_weights"
        / "202605071200_nimrod_xkm_weights.nc"
    )

    saved_paths = [path for _, path in save_calls]
    assert expected_obs_file in saved_paths
    assert expected_weight_file in saved_paths
