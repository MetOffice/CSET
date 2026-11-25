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

"""Tests transect operator."""

import iris
import iris.coord_systems
import numpy as np
import pytest
from iris.coords import DimCoord
from iris.cube import Cube

from CSET.operators.significance import bootstrap_significance


@pytest.fixture
def forecast_reference_time_coord():
    """Create DimCoord object of name forecast_reference_time."""
    return DimCoord(
        np.arange(20),
        long_name="forecast_reference_time",
        units="1",
    )


def make_cube(data, is_base=False):
    """Make a basic cube."""
    attributes = {}

    if is_base:
        attributes["cset_comparison_base"] = 1

    return Cube(
        data,
        long_name="test",
        units="1",
        dim_coords_and_dims=[
            (
                DimCoord(
                    np.arange(data.shape[0]),
                    long_name="forecast_reference_time",
                    units="1",
                ),
                0,
            ),
        ],
        attributes=attributes,
    )


def test_bootstrap_significance_identical():
    """Identical cubes should not be significant."""
    base = make_cube(
        np.arange(20.0),
        is_base=True,
    )

    other = make_cube(
        np.arange(20.0),
    )

    cubes = iris.cube.CubeList([base, other])

    out = bootstrap_significance(
        cubes,
        seed=0,
    )

    assert len(out) == 1
    assert out[0].data == False


def test_bootstrap_significance_constant_offset():
    """Constant offset should be significant."""
    base = make_cube(
        np.arange(20.0),
        is_base=True,
    )

    other = make_cube(
        np.arange(20.0) + 5.0,
    )

    cubes = iris.cube.CubeList([base, other])

    out = bootstrap_significance(
        cubes,
        seed=0,
    )

    assert out[0].data == True


def test_bootstrap_significance_negative_offset():
    """Negative offset should also be significant."""
    base = make_cube(
        np.arange(20.0),
        is_base=True,
    )

    other = make_cube(
        np.arange(20.0) - 5.0,
    )

    cubes = iris.cube.CubeList([base, other])

    out = bootstrap_significance(
        cubes,
        seed=0,
    )

    assert out[0].data


def test_bootstrap_significance_multiple_models():
    """Multiple models can be tested together."""
    base = make_cube(
        np.arange(20.0),
        is_base=True,
    )

    better = make_cube(
        np.arange(20.0) + 2.0,
    )

    same = make_cube(
        np.arange(20.0),
    )

    cubes = iris.cube.CubeList(
        [
            base,
            better,
            same,
        ]
    )

    sig = bootstrap_significance(
        cubes,
        seed=0,
    )

    assert len(sig) == 2

    assert sig[0].data
    assert not sig[1].data


def test_bootstrap_significance_return_intervals():
    """Interval cubes are returned."""
    base = make_cube(
        np.arange(20.0),
        is_base=True,
    )

    other = make_cube(
        np.arange(20.0) + 1.0,
    )

    cubes = iris.cube.CubeList([base, other])

    (
        sig,
        lower,
        upper,
        mean,
    ) = bootstrap_significance(
        cubes,
        seed=0,
        return_intervals=True,
    )

    assert len(sig) == 1
    assert len(lower) == 1
    assert len(upper) == 1
    assert len(mean) == 1


def test_bootstrap_significance_mean_difference():
    """Mean difference should be correct."""
    base = make_cube(
        np.arange(20.0),
        is_base=True,
    )

    other = make_cube(
        np.arange(20.0) + 1.0,
    )

    cubes = iris.cube.CubeList([base, other])

    (
        _,
        _,
        _,
        mean,
    ) = bootstrap_significance(
        cubes,
        seed=0,
        return_intervals=True,
    )

    assert np.isclose(
        mean[0].data,
        1.0,
    )


def test_bootstrap_significance_shape_mismatch():
    """Mismatched input shapes should fail."""
    base = make_cube(
        np.arange(20.0),
        is_base=True,
    )

    other = make_cube(
        np.arange(10.0),
    )

    cubes = iris.cube.CubeList([base, other])

    with pytest.raises(ValueError):
        bootstrap_significance(cubes)


def test_bootstrap_significance_missing_frt():
    """Missing forecast_reference_time should fail."""
    attributes = {"cset_comparison_base": 1}

    base = Cube(
        np.arange(20.0),
        attributes=attributes,
    )

    other = Cube(
        np.arange(20.0),
    )

    cubes = iris.cube.CubeList(
        [
            base,
            other,
        ]
    )

    with pytest.raises(ValueError):
        bootstrap_significance(cubes)


def test_bootstrap_significance_single_frt():
    """Need more than one forecast reference time."""
    base = make_cube(
        [1.0],
        is_base=True,
    )

    other = make_cube(
        [2.0],
    )

    cubes = iris.cube.CubeList([base, other])

    with pytest.raises(ValueError):
        bootstrap_significance(cubes)


def test_bootstrap_significance_invalid_percentiles():
    """Invalid percentile ordering should fail."""
    base = make_cube(
        np.arange(20.0),
        is_base=True,
    )

    other = make_cube(
        np.arange(20.0),
    )

    cubes = iris.cube.CubeList([base, other])

    with pytest.raises(ValueError):
        bootstrap_significance(
            cubes,
            lower_percentile=95,
            upper_percentile=5,
        )


def test_bootstrap_significance_attributes():
    """Bootstrap metadata should be attached."""
    base = make_cube(
        np.arange(20.0),
        is_base=True,
    )

    other = make_cube(
        np.arange(20.0) + 1.0,
    )

    cubes = iris.cube.CubeList([base, other])

    sig = bootstrap_significance(
        cubes,
        n_bootstrap=123,
        lower_percentile=10,
        upper_percentile=90,
        seed=0,
    )

    cube = sig[0]

    assert cube.attributes["bootstrap_n_samples"] == 123

    assert cube.attributes["bootstrap_lower_percentile"] == 10

    assert cube.attributes["bootstrap_upper_percentile"] == 90
