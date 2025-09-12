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

"""Operators for diagnostics related to aviation."""

import logging

import iris
import iris.cube
import numpy as np

from CSET._common import iter_maybe


def aviation_colour_state(
    aviation_state_visibility: iris.cube.Cube | iris.cube.CubeList,
    aviation_state_cloud_base: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Total aviation colour state."""
    aviation_colour_state_list = iris.cube.CubeList([])
    for as_vis, as_cld in zip(
        iter_maybe(aviation_state_visibility),
        iter_maybe(aviation_state_cloud_base),
        strict=True,
    ):
        aviation_colour_state = as_vis.copy()
        # The total aviation colour state is defined by the maximum of that due to
        # visibility or cloud base, therefore to take the maximum of two cubes we
        # use np.max over a specified axis.
        aviation_colour_state.data = np.max([as_vis.data, as_cld.data], axis=0)
        # Rename the cube.
        aviation_colour_state.rename("aviation_colour_state")
        aviation_colour_state_list.append(aviation_colour_state)
    if len(aviation_colour_state_list) == 1:
        return aviation_colour_state_list[0]
    else:
        return aviation_colour_state_list


def aviation_colour_state_visibility(
    visibility: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Aviation colour state due to visibility."""
    aviation_state_visibility_list = iris.cube.CubeList([])

    for vis in iter_maybe(visibility):
        aviation_state_visibility = vis.copy()

        aviation_state_visibility.data[:] = 0.0
        # Calculate the colour state due to visibility.
        # White.
        aviation_state_visibility.data[vis.data < 8.0] += 1.0
        # Green.
        aviation_state_visibility.data[vis.data < 5.0] += 1.0
        # Yellow 1.
        aviation_state_visibility.data[vis.data < 3.7] += 1.0
        # Yellow 2.
        aviation_state_visibility.data[vis.data < 2.5] += 1.0
        # Amber.
        aviation_state_visibility.data[vis.data < 1.6] += 1.0
        # Red.
        aviation_state_visibility.data[vis.data < 0.8] += 1.0

        # Rename and reunit for aviation colour state.
        aviation_state_visibility.units = "1"
        aviation_state_visibility.rename("aviation_colour_state_due_to_visibility")

        aviation_state_visibility_list.append(aviation_state_visibility)

    if len(aviation_state_visibility_list) == 1:
        return aviation_state_visibility_list[0]
    else:
        return aviation_state_visibility_list


def aviation_colour_state_cloud_base(
    cloud_base: iris.cube.Cube | iris.cube.CubeList,
    orography: iris.cube.CubeList | iris.cube.CubeList = None,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Aviation colour state due to cloud base."""
    aviation_state_cloud_base_list = iris.cube.CubeList([])

    # Determine if the cloud base is above sea level or above ground level.

    # Now deal with CubeLists.
    for cld, orog in zip(iter_maybe(cloud_base), iter_maybe(orography), strict=True):
        # Convert the cloud base to above ground level using the orography cube.
        # Check dimensions for Orography cube and replace with 2D array if not 2D.
        if "sea_level" in cld.long_name:
            logging.info("Cloud base given above sea level so subtracting orography.")
            # If cloud base is given above sea level check for an orography cube.
            if orography is None:
                raise ValueError(
                    "An orography cube needs to be provided as data is above sea level."
                )
            # Process orography cube.
            if orog.ndim == 3:
                orog = orog.slices_over("realization").next()
                logging.warning("Orography assumed not to vary with ensemble member")
            elif orog.ndim == 4:
                orog = orog.slices_over(("time", "realization")).next()
                logging.warning(
                    "Orography assumed not to vary with time or ensemble member. "
                )
            # Subtract orography from cloud base altitude.
            cld.data -= orog.data
        else:
            logging.info("Cloud base given above ground level.")

        # Create a cube for the aviation colour state and set all to zero.
        aviation_state_cloud_base = cld.copy()
        aviation_state_cloud_base.data[:] = 0.0

        # Calculate the aviation colour state due to cloud base using the METAR
        # definitions, and adapting them to kilofeet.
        # White.
        aviation_state_cloud_base.data[cld.data < 2.5] += 1.0
        # Green.
        aviation_state_cloud_base.data[cld.data < 1.5] += 1.0
        # Yellow 1.
        aviation_state_cloud_base.data[cld.data < 0.7] += 1.0
        # Yellow 2.
        aviation_state_cloud_base.data[cld.data < 0.5] += 1.0
        # Amber.
        aviation_state_cloud_base.data[cld.data < 0.3] += 1.0
        # Red.
        aviation_state_cloud_base.data[cld.data < 0.2] += 1.0

        # Rename and reunit the cube for aviation colour state.
        aviation_state_cloud_base.units = "1"
        aviation_state_cloud_base.rename(
            "aviation_colour_state_due_to_cloud_base_gt_2p5_oktas"
        )

        aviation_state_cloud_base_list.append(aviation_state_cloud_base)

    if len(aviation_state_cloud_base_list) == 1:
        return aviation_state_cloud_base_list[0]
    else:
        return aviation_state_cloud_base_list
