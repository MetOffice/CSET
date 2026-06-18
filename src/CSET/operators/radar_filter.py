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

import logging

import iris
import iris.cube
import iris.exceptions
import numpy as np

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
    >>> land_points_only = apply_mask(temperature, land_mask)
    """
    print("original_field cube: ", original_field)
    print("mask cube", mask)

    # Create an empty cubelist to hold the filtered fields.
    masked_fields = iris.cube.CubeList([])

    # Loop over the input mask and field cubes.
    for M, F in zip(iter_maybe(mask), iter_maybe(original_field), strict=True):
        # Ensure mask data are floats and only 1s or NaNs.
        print(" type(M.data)", type(M.data))
        M.data = np.float64(M.data)
        M.data[M.data == 0.0] = np.nan
        M.data[~np.isnan(M.data)] = 1.0
        print(" type(M.data) v2", type(M.data))
        print("---> M[0][300][:].data ", M[0][300][:].data)
        print(
            "---> max(M) ", max(M[0][300][:].data), " min(M) ", min(M[0][300][:].data)
        )
        logging.info(
            "Mask set to 1 or 0s, if addition of multiple masks results"
            "in values > 1 these are set to 1."
        )

        print("")
        print("---> here is F[0]")
        print(F[0])
        print("")

        print("")
        print("---> here is F[1]")
        print(F[1])
        print("")

        #        print("")
        #        print("---> here is F[24]")
        #        print(F[24])
        #        print("")

        # Apply the mask
        masked_field = F.copy()
        print(" M.shape is ", M.shape)
        print(" masked_field.shape is ", masked_field.shape)
        print(" M[0].shape is ", M[0].shape)
        print(" masked_field[0].shape is ", masked_field[0].shape)

        # If the field and mask on on different grids, then regrid the field.
        if M[0].shape != masked_field[0].shape:
            regridded_cube = masked_field.regrid(M, iris.analysis.Linear())
            masked_field = regridded_cube

            print(" ---> Have regridded the field")

            print("")
            print("---> here is masked_field[0]")
            print(masked_field[0])
            print("")

            print(" M.shape is ", M.shape)
            print(" masked_field.shape is ", masked_field.shape)
            print(" M[0].shape is ", M[0].shape)
            print(" masked_field[0].shape is ", masked_field[0].shape)

        print("")
        print("---> check how many time instances there are of both field and mask")
        print("---> masked_field.shape[0] ", masked_field.shape[0])
        print("---> M.shape[0] ", M.shape[0])

        print("")
        # print("---> max(M)", max(list(M.data)))

        loop_i = min(M.shape[0], masked_field.shape[0])
        for i in range(loop_i):
            print("  i is ", i)
            # print("---> max(M[i]) ", max(M[i].data), " min(M[i]) ", min(M[i].data))
            # print("---> max(M[i]) ", max(list(M[i].data)), " min(M[i]) ", min(list(M[i].data)))
            # masked_field[i].data *= M[i].data
            # masked_field[i] = apply_mask(masked_field[i], M[i])
            # mask_array = M[i][:][:].data.filled(np.array)
            mask_array = M[i].data.filled(np.array)
            print(" type(M.data)", type(M.data))
            print(" type(mask_array)", type(mask_array))
            masked_field[i][:][:].data *= mask_array
            # masked_field[i][:][:].data *= M[i][:][:].data
            # print("---> max(mask_array) ", max(mask_array), " min(mask_array ) ", min(mask_array) )
            print(
                "---> max(M[i][300]) ",
                max(M[i][300].data),
                " min(M[i][300]) ",
                min(M[i][300].data),
            )
            print(
                "---> max(F[i][300]) ",
                max(masked_field[i][300].data),
                " min(F[i][300]) ",
                min(masked_field[i][300].data),
            )
            # print("  check 1 ")
            masked_field[i].attributes["mask"] = f"mask_of_{F.name()}"
            # print("  check 2 ")
            masked_fields.append(masked_field[i])

    #        if M[0].shape == F[0].shape:
    #          masked_field.data *= M.data
    #        masked_field.attributes["mask"] = f"mask_of_{F.name()}"
    #        masked_fields.append(masked_field)

    print(" len(masked_fields) ", len(masked_fields))
    if len(masked_fields) == 1:
        return masked_fields[0]
    else:
        # return masked_fields
        return masked_fields.merge()
