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

"""Tests for aviation diagnostics."""

import cf_units
import iris
import iris.cube
import numpy as np
import pytest

from CSET.operators import aviation


def test_aviation_colour_state(visibility_cube, cloud_base_cube, orography_cube):
    """Check that the aviation colour state is calculated."""
    vis = aviation.aviation_colour_state_visibility(visibility=visibility_cube)
    cld = aviation.aviation_colour_state_cloud_base(
        cloud_base=cloud_base_cube, orography=orography_cube
    )
    expected_max = visibility_cube.copy()
    expected_max.data[:] = 0.0
    expected_max.data = np.max([vis.data, cld.data], axis=0)
    assert np.allclose(
        expected_max.data,
        aviation.aviation_colour_state(vis, cld).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_aviation_colour_state_name(visibility_cube, cloud_base_cube, orography_cube):
    """Check aviation colour state cube has expected name."""
    expected_name = "aviation_colour_state"
    vis = aviation.aviation_colour_state_visibility(visibility=visibility_cube)
    cld = aviation.aviation_colour_state_cloud_base(
        cloud_base=cloud_base_cube, orography=orography_cube
    )
    assert expected_name == aviation.aviation_colour_state(vis, cld).name()


def test_aviation_colour_sate_cubelist(
    visibility_cube, cloud_base_cube, orography_cube
):
    """Check aviation colour state handles a CubeList."""
    vis = aviation.aviation_colour_state_visibility(visibility=visibility_cube)
    cld = aviation.aviation_colour_state_cloud_base(
        cloud_base=cloud_base_cube, orography=orography_cube
    )
    expected_max = visibility_cube.copy()
    expected_max.data[:] = 0.0
    expected_max.data = np.max([vis.data, cld.data], axis=0)
    expected_cubelist = iris.cube.CubeList([expected_max, expected_max])
    vis_list = iris.cube.CubeList([vis, vis])
    cld_list = iris.cube.CubeList([cld, cld])
    actual_max_list = aviation.aviation_colour_state(vis_list, cld_list)
    for cube_a, cube_b in zip(expected_cubelist, actual_max_list, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_aviation_colour_state_visibility(visibility_cube):
    """Check that the aviation colour state due to visibility is calculated."""
    expected_data = visibility_cube.copy()
    expected_data.data[:] = 0.0
    expected_data.data[visibility_cube.data < 8.0] += 1.0
    expected_data.data[visibility_cube.data < 5.0] += 1.0
    expected_data.data[visibility_cube.data < 3.7] += 1.0
    expected_data.data[visibility_cube.data < 2.5] += 1.0
    expected_data.data[visibility_cube.data < 1.6] += 1.0
    expected_data.data[visibility_cube.data < 0.8] += 1.0

    assert np.allclose(
        expected_data.data,
        aviation.aviation_colour_state_visibility(visibility=visibility_cube).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_aviation_colour_state_visibility_name(visibility_cube):
    """Check that the output cube has the expected name."""
    expected_name = "aviation_colour_state_due_to_visibility"
    assert (
        expected_name
        == aviation.aviation_colour_state_visibility(visibility_cube).name()
    )


def test_aviaiton_color_state_visibility_unit(visibility_cube):
    """Check that the output cube has the expected units."""
    expected_units = cf_units.Unit("1")
    assert (
        expected_units
        == aviation.aviation_colour_state_visibility(visibility_cube).units
    )


def test_aviation_colour_state_visibility_cube_list(visibility_cube):
    """Check that the aviation colour state due to visibility is calculated for a CubeList."""
    expected_data = visibility_cube.copy()
    expected_data.data[:] = 0.0
    expected_data.data[visibility_cube.data < 8.0] += 1.0
    expected_data.data[visibility_cube.data < 5.0] += 1.0
    expected_data.data[visibility_cube.data < 3.7] += 1.0
    expected_data.data[visibility_cube.data < 2.5] += 1.0
    expected_data.data[visibility_cube.data < 1.6] += 1.0
    expected_data.data[visibility_cube.data < 0.8] += 1.0
    expected_list = iris.cube.CubeList([expected_data, expected_data])
    input_cubelist = iris.cube.CubeList([visibility_cube, visibility_cube])
    actual_cubelist = aviation.aviation_colour_state_visibility(input_cubelist)
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_aviation_colour_state_cloud_base(cloud_base_cube, orography_cube):
    """Check that aviation colour state due to cloud base is calculated."""
    expected_data = cloud_base_cube.copy()
    expected_data.data[:] = 0.0
    expected_data.data[(cloud_base_cube.data - orography_cube.data) < 2.5] += 1.0
    expected_data.data[(cloud_base_cube.data - orography_cube.data) < 1.5] += 1.0
    expected_data.data[(cloud_base_cube.data - orography_cube.data) < 0.7] += 1.0
    expected_data.data[(cloud_base_cube.data - orography_cube.data) < 0.5] += 1.0
    expected_data.data[(cloud_base_cube.data - orography_cube.data) < 0.3] += 1.0
    expected_data.data[(cloud_base_cube.data - orography_cube.data) < 0.2] += 1.0

    assert np.allclose(
        expected_data.data,
        aviation.aviation_colour_state_cloud_base(
            cloud_base=cloud_base_cube, orography=orography_cube
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_aviation_colour_state_cloud_base_name(cloud_base_cube, orography_cube):
    """Check that the output cube has the expected name."""
    expected_name = "aviation_colour_state_due_to_cloud_base_gt_2p5_oktas"
    assert (
        expected_name
        == aviation.aviation_colour_state_cloud_base(
            cloud_base=cloud_base_cube, orography=orography_cube
        ).name()
    )


def test_aviation_colour_state_cloud_base_units(cloud_base_cube, orography_cube):
    """Check that the output cube has the expected units."""
    expected_units = cf_units.Unit("1")
    assert (
        expected_units
        == aviation.aviation_colour_state_cloud_base(
            cloud_base=cloud_base_cube, orography=orography_cube
        ).units
    )


def test_aviation_colour_state_cloud_base_cubelist(cloud_base_cube, orography_cube):
    """Check that aviation colour state due to cloud base is calculated for a cube list."""
    expected_data = cloud_base_cube.copy()
    expected_data.data[:] = 0.0
    expected_data.data[(cloud_base_cube.data - orography_cube.data) < 2.5] += 1.0
    expected_data.data[(cloud_base_cube.data - orography_cube.data) < 1.5] += 1.0
    expected_data.data[(cloud_base_cube.data - orography_cube.data) < 0.7] += 1.0
    expected_data.data[(cloud_base_cube.data - orography_cube.data) < 0.5] += 1.0
    expected_data.data[(cloud_base_cube.data - orography_cube.data) < 0.3] += 1.0
    expected_data.data[(cloud_base_cube.data - orography_cube.data) < 0.2] += 1.0
    expected_list = iris.cube.CubeList([expected_data, expected_data])
    input_cloud = iris.cube.CubeList([cloud_base_cube, cloud_base_cube])
    input_orography = iris.cube.CubeList([orography_cube, orography_cube])
    actual_cubelist = aviation.aviation_colour_state_cloud_base(
        cloud_base=input_cloud, orography=input_orography
    )
    for cube_a, cube_b in zip(expected_list, actual_cubelist, strict=True):
        assert np.allclose(cube_a.data, cube_b.data, rtol=1e-6, atol=1e-2)


def test_aviation_colour_state_cloud_base_above_ground_level(cloud_base_cube):
    """Check that aviation colour state due to cloud base is calculated for above ground level data."""
    cloud_base_cube.rename(
        "cloud_base_altitude_above_ground_level_for_greater_than_2p5_oktas_coverage"
    )
    expected_data = cloud_base_cube.copy()
    expected_data.data[:] = 0.0
    expected_data.data[cloud_base_cube.data < 2.5] += 1.0
    expected_data.data[cloud_base_cube.data < 1.5] += 1.0
    expected_data.data[cloud_base_cube.data < 0.7] += 1.0
    expected_data.data[cloud_base_cube.data < 0.5] += 1.0
    expected_data.data[cloud_base_cube.data < 0.3] += 1.0
    expected_data.data[cloud_base_cube.data < 0.2] += 1.0
    assert np.allclose(
        expected_data.data,
        aviation.aviation_colour_state_cloud_base(cloud_base=cloud_base_cube).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_aviation_colour_state_cloud_base_sea_level_error(cloud_base_cube):
    """Check that an error is raised when data is above sea level and orography cube not given."""
    cloud_base_cube.rename(
        "cloud_base_altitude_above_sea_level_for_greater_than_2p5_oktas_coverage"
    )
    with pytest.raises(
        ValueError,
        match="An orography cube needs to be provided as data is above sea level.",
    ):
        aviation.aviation_colour_state_cloud_base(
            cloud_base=cloud_base_cube, orography=None
        )


def test_aviation_colour_state_cloud_base_3D_orography(
    cloud_base_cube, orography_3D_cube
):
    """Check that a 3D orography cube is handled correctly."""
    cloud_base_cube.rename(
        "cloud_base_altitude_above_sea_level_for_greater_than_2p5_oktas_coverage"
    )
    expected_data = cloud_base_cube.copy()
    expected_data.data[:] = 0.0
    expected_data.data[(cloud_base_cube.data - orography_3D_cube.data[0, :]) < 2.5] += (
        1.0
    )
    expected_data.data[(cloud_base_cube.data - orography_3D_cube.data[0, :]) < 1.5] += (
        1.0
    )
    expected_data.data[(cloud_base_cube.data - orography_3D_cube.data[0, :]) < 0.7] += (
        1.0
    )
    expected_data.data[(cloud_base_cube.data - orography_3D_cube.data[0, :]) < 0.5] += (
        1.0
    )
    expected_data.data[(cloud_base_cube.data - orography_3D_cube.data[0, :]) < 0.3] += (
        1.0
    )
    expected_data.data[(cloud_base_cube.data - orography_3D_cube.data[0, :]) < 0.2] += (
        1.0
    )
    assert np.allclose(
        expected_data.data,
        aviation.aviation_colour_state_cloud_base(
            cloud_base=cloud_base_cube, orography=orography_3D_cube
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )


def test_aviation_colour_state_cloud_base_4D_orography(
    cloud_base_cube, orography_4D_cube
):
    """Check that a 4D orography cube is handled correctly."""
    cloud_base_cube.rename(
        "cloud_base_altitude_above_sea_level_for_greater_than_2p5_oktas_coverage"
    )
    expected_data = cloud_base_cube.copy()
    expected_data.data[:] = 0.0
    expected_data.data[
        (cloud_base_cube.data - orography_4D_cube.data[0, 0, :]) < 2.5
    ] += 1.0
    expected_data.data[
        (cloud_base_cube.data - orography_4D_cube.data[0, 0, :]) < 1.5
    ] += 1.0
    expected_data.data[
        (cloud_base_cube.data - orography_4D_cube.data[0, 0, :]) < 0.7
    ] += 1.0
    expected_data.data[
        (cloud_base_cube.data - orography_4D_cube.data[0, 0, :]) < 0.5
    ] += 1.0
    expected_data.data[
        (cloud_base_cube.data - orography_4D_cube.data[0, 0, :]) < 0.3
    ] += 1.0
    expected_data.data[
        (cloud_base_cube.data - orography_4D_cube.data[0, 0, :]) < 0.2
    ] += 1.0
    assert np.allclose(
        expected_data.data,
        aviation.aviation_colour_state_cloud_base(
            cloud_base=cloud_base_cube, orography=orography_4D_cube
        ).data,
        rtol=1e-6,
        atol=1e-2,
    )
