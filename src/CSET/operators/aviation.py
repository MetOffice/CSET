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
    """Total aviation colour state.

    Parameters
    ----------
    aviation_state_visibility: iris.cube.Cube | iris.cube.CubeList
        A Cube or CubeList of the aviation state due to visibility.
    aviation_state_cloud_base: iris.cube.Cube | iris.cube.CubeList
        A Cube or CubeList of the aviation state due to cloud base altitude.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList

    Notes
    -----
    The aviation colour state is a colour-coded diagnostic that summarises
    weather conditions at an airfield.

    The aviation colour state is the maximum (i.e. worst conditions) from the
    aviation colour state due to visibility and cloud base altitude. For the
    purposes of this diagnostic we use the military airfield definition as would
    be found on METARs. The table below from the `Met Office website <https://www.metoffice.gov.uk/services/transport/aviation/regulated/national-aviation/abs/faqs>`__ shows the minimum
    weather conditions required for each colour. The redder the colour state
    the poorer the conditions at the aerodrome.

    .. list-table:: Aviation Colour State
       :widths: 10 10 10
       :header-rows: 1

       * - Aerodrome Colour State
         - Surface visibility
         - Base of lowest cloud layer of 3/8 (SCT) or more in heights above ground level
       * - Blue (BLU)
         - 8.0 km
         - 2.5 kft
       * - White (WHT)
         - 5.0 km
         - 1.5 kft
       * - Green (GRN)
         - 3.7 km
         - 0.7 kft
       * - Yellow 1 (YLO1)
         - 2.5 km
         - 0.5 kft
       * - Yellow 2 (YLO2)
         - 1.6 km
         - 0.3 kft
       * - Amber (AMB)
         - 0.8 km
         - 0.2 kft
       * - Red (RED)
         - < 0.8 km
         - < 0.2 kft


    Examples
    --------
    >>> ACS = aviation.aviation_colour_state(vis,cloud_base)
    """
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
    """Aviation colour state due to visibility.

    Parameters
    ----------
    visibility: iris.cube.Cube | iris.cube.CubeList
        A Cube or CubeList of the screen level visibility.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList

    Notes
    -----
    The aviation colour state due to visibility is a colour-coded diagnostic
    that summarises the visibility conditions at an airfield. The visibility
    is from any source (e.g. precipitation and fog).

    For the purposes of this diagnostic we use the military airfield definition
    as would be found on METARs. The table below from the `Met Office website <https://www.metoffice.gov.uk/services/transport/aviation/regulated/national-aviation/abs/faqs>`__ shows the minimum
    weather conditions required for each colour. The redder the colour state
    the poorer the visibility conditions at the aerodrome.

    .. list-table:: Aviation Colour State due to Visibility
       :widths: 10 10
       :header-rows: 1

       * - Aerodrome Colour State
         - Surface visibility
       * - Blue (BLU)
         - 8.0 km
       * - White (WHT)
         - 5.0 km
       * - Green (GRN)
         - 3.7 km
       * - Yellow 1 (YLO1)
         - 2.5 km
       * - Yellow 2 (YLO2)
         - 1.6 km
       * - Amber (AMB)
         - 0.8 km
       * - Red (RED)
         - < 0.8 km


    Examples
    --------
    >>> ACS = aviation.aviation_colour_state_visibility(vis)
    """
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
    """Aviation colour state due to cloud base.

    Parameters
    ----------
    cloud_base: iris.cube.Cube | iris.cube.CubeList
        A Cube or CubeList of the cloud base altitude.
    orography: iris.cube.Cube | iris.cube.CubeList, None, optional
        A Cube or CubeList of the orography. The default is None.
        This field should be included if your cloud_base_altitude is
        defined above sea level as the colour states are defined for
        aerodromes above ground level.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList

    Notes
    -----
    The aviation colour state is a colour-coded diagnostic that summarises
    cloud base altitude above ground level at an airfield.

    For the purposes of this diagnostic we use the military airfield definition as would
    be found on METARs. The table below from the `Met Office website <https://www.metoffice.gov.uk/services/transport/aviation/regulated/national-aviation/abs/faqs>`__ shows the minimum
    weather conditions required for each colour. The redder the colour state
    the lower the cloud base at the aerodrome.

    .. list-table:: Aviation Colour State due to Cloud Base Altitude
       :widths: 10 10
       :header-rows: 1

       * - Aerodrome Colour State
         - Base of lowest cloud layer of 3/8 (SCT) or more in heights above ground level
       * - Blue (BLU)
         - 2.5 kft
       * - White (WHT)
         - 1.5 kft
       * - Green (GRN)
         - 0.7 kft
       * - Yellow 1 (YLO1)
         - 0.5 kft
       * - Yellow 2 (YLO2)
         - 0.3 kft
       * - Amber (AMB)
         - 0.2 kft
       * - Red (RED)
         - < 0.2 kft

    You might encounter warnings with the following text ``An orography cube should
    be provided if cloud base altitude is above sea level. Please check your cloud
    base altitude definition and adjust if required.`` when you do not define an
    orography file. This warning is to ensure that the cloud base is defined above
    ground level. Should your cloud base be defined above sea level and this warning
    appears please correct and define an orography field so that the height correction
    can take place.

    You might further encounter warnings with the following text ``Orography assumed not
    to vary with ensemble member.`` or ``Orography assumed not to vary with time
    and ensemble member.`` these warnings are expected when the orography files
    are not 2-dimensional, and do not cause any problems unless ordering is not
    as expected.

    Examples
    --------
    >>> # If cloud base is defined above sea level.
    >>> ACS = aviation.aviation_colour_state_cloud_base(cloud_base,orography)
    >>> # If cloud base is defined above ground level.
    >>> ACS = aviation.aviation_colour_state_cloud_base(cloud_base)
    """
    aviation_state_cloud_base_list = iris.cube.CubeList([])

    # Determine if the cloud base is above sea level or above ground level.

    # Now deal with CubeLists.
    for cld, orog in zip(iter_maybe(cloud_base), iter_maybe(orography), strict=True):
        # Convert the cloud base to above ground level using the orography cube.
        # Check dimensions for Orography cube and replace with 2D array if not 2D.
        if orography is None:
            logging.warning(
                "An orography cube should be provided if cloud base altitude is above sea level. Please check your cloud base altitude definition and adjust if required."
            )
        else:
            logging.info("Cloud base given above ground level using orography.")
            # Process orography cube.
            if orog.ndim == 3:
                orog = orog.slices_over("realization").next()
                logging.warning("Orography assumed not to vary with ensemble member")
            elif orog.ndim == 4:
                orog = orog.slices_over(("time", "realization")).next()
                logging.warning(
                    "Orography assumed not to vary with time or ensemble member. "
                )
            # Subtract orography from cloud base altitude after converting to same units.
            orog.convert_units("kilofeet")
            cld.data -= orog.data

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
