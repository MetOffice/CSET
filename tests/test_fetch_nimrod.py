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

from datetime import datetime
from types import SimpleNamespace

import numpy as np

from CSET.cset_workflow.app.fetch_nimrod.bin.fetch_nimrod import (
    _get_needed_environment_variables_nimrod,
    apply_radar_weights,
)


# Tests for apply_radar_weights
def make_cube(data):
    """Form a cube of test data from an array."""
    return SimpleNamespace(data=np.array(data))


def test_apply_radar_weights_leaves_good_values_and_zeroes_bad():
    """Test that Nimrod weights are correctly applied to hourly rainfall accumulations."""
    obs = make_cube([[1.0, 2.0], [3.0, 4.0]])
    weights = make_cube([[11, 12], [10, 13]])

    obs_out, wei_out = apply_radar_weights(obs, weights)

    assert np.array_equal(wei_out.data, np.array([[11, 12], [10, 13]]))
    assert np.array_equal(obs_out.data, np.array([[1.0, 2.0], [0.0, 4.0]]))


def test_apply_radar_weights_unpack_packed_weights():
    """Test that Nimrod weights are correctly unpacked."""
    obs = make_cube([[1.0, 2.0], [3.0, 4.0]])
    packed = make_cube([[13 / 32, 12 / 32], [10 / 32, 11 / 32]])

    obs_out, wei_out = apply_radar_weights(obs, packed)

    assert np.array_equal(wei_out.data, np.array([[13, 12], [10, 11]]))
    assert np.array_equal(obs_out.data, np.array([[1.0, 2.0], [0.0, 4.0]]))

    obs = make_cube([[1.0, 2.0], [3.0, 4.0]])
    packed = make_cube([[13, 12], [10, 11]])

    obs_out, wei_out = apply_radar_weights(obs, packed)

    assert np.array_equal(wei_out.data, np.array([[13, 12], [10, 11]]))
    assert np.array_equal(obs_out.data, np.array([[1.0, 2.0], [0.0, 4.0]]))


# Tests for env loading and parsing logic.
def test_get_needed_environment_variables_nimrod(monkeypatch):
    """Test the environment variables required to fetch Nimrod data."""
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
