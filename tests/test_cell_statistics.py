# Copyright 2023 Met Office and contributors.
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

"""Tests for cell statistics functionality across CSET."""

from pathlib import Path
import pytest
import CSET.operators.cell_statistics as cs
import glob
import iris

def test_cell_effective_radius():
    """Happy case for cell effective raduis."""
    files = glob.glob("/tests/test_data/precip_cubes*.nc")
    cubelist = iris.load(files)
    input_params = {
        "thresholds": [0.5],
        "time_grouping": "forecast_period",
        "cell_attribute": "effective_radius_in_km",
        "plot_dir": "/test/test_data/"
    }
    
    assert cs.cell_statistics(cubelist,input_params) == 0


def test_cell_mean_size():
    """Happy case for cell mean size."""
    files = glob.glob("/tests/test_data/precip_cubes*.nc")
    cubelist = iris.load(files)
    input_params = {
        "thresholds": [0.5],
        "time_grouping": "forecast_period",
        "cell_attribute": "mean_value",
        "plot_dir": "/test/test_data/"
    }
    
    assert cs.cell_statistics(cubelist,input_params) == 0

def test_cubelist_is_none():
    """Test exception for null cubelist"""
    cubelist = None
    input_params = {
        "thresholds": [0.5],
        "time_grouping": "forecast_period",
        "cell_attribute": "mean",
        "plot_dir": "/test/test_data/"
    }
    with pytest.raises(Exception):
        cs.cell_statistics(cubelist, input_params)

def test_cell_attribute_unknown():
    """Test exception for unknown cell attribute"""
    files = glob.glob("/tests/test_data/precip_cubes*.nc")
    cubelist = iris.load(files)
    input_params = {
        "thresholds": [0.5],
        "time_grouping": "forecast_period",
        "cell_attribute": "mean_cell",
        "plot_dir": "/test/test_data/"
    }
    with pytest.raises(Exception):
        cs.cell_statistics(cubelist, input_params)