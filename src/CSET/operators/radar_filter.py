# © Crown copyright, Met Office (2022-2026) and CSET contributors.
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

"""Operators to perform various kind of filtering."""

import iris
import iris.cube
import iris.exceptions

from CSET._common import iter_maybe
from CSET.operators.filters import apply_mask, generate_mask


def mask_list(model_names: list[str]) -> list[str]:
    """Determine the Nimrod weights files to use.

    Parameters
    ----------
    model_names: list[str]
        A list of model and Nimrod hourly rainfall accumulation files.

    Returns
    -------
    list[str]
        A list of the Nimrod weights files to use with each of the input
        model / observations files.

    Notes
    -----
     At lest one of the entries in the input list must be a Nimrod hourly
     rainfall accumulation file.

     If just one Nimrod file is specified, then then the weights file associated
     with this field is used.

     If more than one Nimrod file is in the input list, then each of the these
     Nimrod files is associated with its own weights file e.g. if the input list
     contains ["Nimrod1km", "Nimrod2km"] then the weights files for these will
     be ["Nimrod1km_weights", "Nimrod2km_weights"]. Any model fields in the input
     list will be allocated a weights file according to the order of preference
     specified in the list nimrod_preference e.g. if the input list is
     ["UM_model", "Nimrod1km", "Nimrod2km"] then the output weights files list will
     be ["Nimrod2km_weights", "Nimrod1km_weights", "Nimrod2km_weights"] as the Nimrod
     weights for 2km data are preferred over those for 1km.

    Examples
    --------
     >>> list_weights = make_list( ["UM_model", "Nimrod1km", "Nimrod2km"] )
     >>> print(list_weights)
     ["Nimrod2km_weights", "Nimrod1km_weights", "Nimrod2km_weights"]

    """
    # Set the preference order for choosing a Nimrod radar weights source
    # in order of most to least preferred.
    nimrod_preference = [
        "Nimrod2km",
        "Nimrod_2km",
        "Nimrodxkm",
        "Nimrod_xkm",
        "Nimrod1km",
        "Nimrod_1km",
    ]

    # Define the string that helps form a Nimrod weights file.
    wei = "_weights"

    # Determine the preferred Nimrod mask to use.
    empty_string = ""
    preferred_nimrod = empty_string
    for prefer in reversed(nimrod_preference):
        if any(prefer in model for model in model_names):
            preferred_nimrod = prefer

    # Create the list of the required Nimrod masks.
    mask_names_list = []
    if preferred_nimrod != empty_string:
        # Loop over the input model_names.
        for model in model_names:
            if any(model in nimrod for nimrod in nimrod_preference):
                nimrod_mask = model + wei
            else:
                nimrod_mask = preferred_nimrod + wei
            mask_names_list.append(nimrod_mask)

    return mask_names_list


def mask_by_weights(
    cubes: iris.cube.CubeList,
    model_names: list[str],
    weights_names: list[str],
    **kwargs,
) -> iris.cube.CubeList:
    """Filter a field using a second field as a mask.

    Parameters
    ----------
    cubes: iris.cube.CubeList
        Two cubes containing the radar observations and their weights.

    Returns
    -------
    Cube

    Raises
    ------
    ValueError, iris.exceptions.NotYetImplementedError
        When the cubes are not compatible.

    Notes
    -----
    This is a simple operator designed for combination of diagnostics or
    creating new diagnostics by using recipes.

    Examples
    --------
    >>> field_filtered = mask_by_weights(cubelist, model_names)

    """
    print("model_names are: ", model_names)
    print("weights_names", weights_names)

    for cube in cubes:
        print("  cube.var_name ", cube.var_name)
        print("    cube.name ", cube.name)
        print("    cube: ")
        print(cube)
        print("    cube.attributes.model_name ", cube.attributes["model_name"])

    # Check the input unfiltered cubes and the mask cubes are both cubelists
    # with the same number of cubes. If not, then add extra mask cubes.
    if len(model_names) != len(weights_names):
        weights_names = mask_list(model_names)

    # Create an empty cubelist to hold the filtered fields.
    filtered_list = iris.cube.CubeList([])

    # Loop over the fields to filter.
    var_constraint = iris.NameConstraint(var_name="hourly_rain_accumulation")
    mask_var_constraint = iris.NameConstraint(var_name="hourly_wts_accumulation")
    for model, mask in zip(
        iter_maybe(model_names),
        iter_maybe(weights_names),
        strict=True,
        #        iter_maybe(model_names), iter_maybe(weights_names), strict=True
    ):
        print(" model, mask ", model, mask)

        # grab the field to filter
        model_constraint = iris.AttributeConstraint(model_name=model)
        unfiltered_field = cubes.extract_cube(var_constraint & model_constraint)

        # Select the field to use as the mask.
        # Nice to do - put in support for a static mask.
        mask_constraint = iris.AttributeConstraint(model_name=mask)
        mask_field = cubes.extract_cube(mask_var_constraint & mask_constraint)

        # Create the mask - note that the condition e.g. "ge" can be set by a loader
        # as can the threshold value.
        mask_radar_wts = generate_mask(mask_field, "ge", 11)

        # print(" This is cube radar_obs: ", radar_obs)
        # print(" This is cube radar_weights: ", radar_wts)
        # print(" This is cube unfiltered: ", unfiltered_field)

        # check the coords of the unfiltered field and the mask field.
        # If these do not match, then regrid the unfiltered field onto
        # the grid used for the mask field.
        # For radar weights fields can use the function regrid_onto_xyspacing in regrid.py,
        # but then might have to extract a subarea to match the mask grid.
        # Might have to consider serval cases for regridding:
        #  (1) model_field(lat, lon) to radar_weights_field(x, y)
        #  (2) model_field(lat, lon) to other_model_field(lat, lon)
        #  (3) Nimrod_field(x, y) to radar_weights_field(x, y)
        #  (4) Nimrod_field(x, y) to model_field(lat,lon) ?
        #

        # Apply the mask.
        masked_radar_obs = apply_mask(unfiltered_field, mask_radar_wts)

        # Put the filtered cube into the list of filtered cubes.
        filtered_list.append(masked_radar_obs)

    # Preserve returning a cube if only a cube has been supplied to filter.
    if len(filtered_list) == 1:
        return filtered_list[0]
    else:
        return filtered_list


def radar_apply_mask(
    original_field: iris.cube.Cube | iris.cube.CubeList,
    mask: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Apply a mask to given data as a masked array.

    Parameters
    ----------
    original_field: iris.cube.Cube | iris.cube.CubeList
        The field(s) to be masked.
    mask: iris.cube.Cube | iris.cube.CubeList
        The mask(s) being applied to the original field(s).

    Returns
    -------
    masked_field: iris.cube.Cube | iris.cube.CubeList
        A cube or cubelist of the masked field(s).

    Notes
    -----
    The mask is first converted to 1s and NaNs before multiplication with
    the original data.

    As discussed in generate_mask, you can combine multiple masks in a
    recipe using other functions before applying the mask to the data.

    Examples
    --------
    >>> land_points_only = radar_apply_mask( surface_microphysical_rainfall_rate, Nimrod2km)
    """
    # Create an empty cubelist to hold the filtered fields.
    masked_fields = iris.cube.CubeList([])

    # Loop over the input mask and field cubes.
    for M, F in zip(iter_maybe(mask), iter_maybe(original_field), strict=True):
        masked_field = F.copy()

        # If the field and mask are on different grids, then regrid the field.
        if M[0].shape != masked_field[0].shape:
            masked_field = masked_field.regrid(M, iris.analysis.Linear())

        # Apply the mask.
        min_timesteps = min(M.shape[0], masked_field.shape[0])
        masked_field = apply_mask(masked_field[0:min_timesteps], M[0:min_timesteps])

        # Attach and attribute to the masked field detailing the mask used.
        masked_field.attributes["mask"] = f"mask_of_{F.name()}"

        # Append the masked field to the output list of masked fields.
        masked_fields.append(masked_field)

    # Return either a single cube or a cubelist.
    if len(masked_fields) == 1:
        return masked_fields[0]
    else:
        # return masked_fields
        return masked_fields.merge()
