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
     >>> list_weights = mask_list( ["UM_model", "Nimrod1km", "Nimrod2km"] )
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
    boundary_margin: int = 8,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Apply a mask to given data as a masked array.

    Parameters
    ----------
    original_field: iris.cube.Cube | iris.cube.CubeList
        The field(s) to be masked.
    mask: iris.cube.Cube | iris.cube.CubeList
        The mask(s) being applied to the original field(s).
    boundary_margin: int, optional
        Number of grid points from the domain boundary considered "unreliable".
        Defaults to 8.

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

        # TODO set the model perimeter to NaN as these gridpoints contain no data.
        # c.f. boundary_margin in regrid.py
        # Get bounds
        # Get axis
        # lat, lon = M.coord(y_coord), M.coord(x_coord)
        # lat_min, lon_min = lat.points.min(), lon.points.min()
        # lat_max, lon_max = lat.points.max(), lon.points.max()
        margin_width = boundary_margin
        if margin_width > 0:
            masked_field.data[:, -margin_width - 1 :, :] = np.nan
            masked_field.data[:, :, -margin_width - 1 :] = np.nan
            masked_field.data[:, :, 0:margin_width] = np.nan
            masked_field.data[:, 0:margin_width, :] = np.nan
        # masked_field.data[:, -margin_width-1:-1, :] = 3.0
        # masked_field.data[:, :, -margin_width-1:-1] = 1.5
        # masked_field.data[:, :, 0:margin_width] = 50.0
        # masked_field.data[:, 0:margin_width, :] = 30.0
        # masked_field.data[ masked_field.data < 0.01 ] = 200.0
        # masked_field.data[ masked_field.data == np.nan ] = 20.0

        # TODO must mask the radar obs using the model domain

        # If the field and mask are on different grids, then regrid the field.
        if M[0].shape != masked_field[0].shape:
            scheme = iris.analysis.Linear(extrapolation_mode="nan")
            masked_field = masked_field.regrid(M, scheme)

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


def radar_mask(
    model_field: iris.cube.Cube | iris.cube.CubeList,
    nimrod_field: iris.cube.Cube | iris.cube.CubeList,
    nimrod_mask: iris.cube.Cube | iris.cube.CubeList,
    boundary_margin: int = 8,
    outputs: str = "Nimrod",
) -> iris.cube.Cube | iris.cube.CubeList:
    """Apply a mask to given data as a masked array."""
    # Create an empty cubelist to hold the filtered fields.
    filtered_fields = iris.cube.CubeList([])
    filtered_radar = iris.cube.CubeList([])
    filtered_model = iris.cube.CubeList([])

    # ensure the three inputs to this function are model_field, nimrod_field, nimrod_mask

    for M, F, N in zip(
        iter_maybe(nimrod_mask),
        iter_maybe(model_field),
        iter_maybe(nimrod_field),
        strict=True,
    ):
        #        masked_field = F.copy()

        # apply the function radar_apply_mask to generate the re-gridded and masked model_field
        # i.e. generate masked_model_field
        masked_model_field = radar_apply_mask(F, M, boundary_margin=boundary_margin)

        # use the model_field as the mask for the nimrod_field - note: no re-gridding required
        # i.e. generate masked_nimrod_field

        min_timesteps = min(N.shape[0], masked_model_field.shape[0])

        temp_mask = masked_model_field[0:min_timesteps].copy()
        # temp_mask.data[ temp_mask.data != np.nan ] = 1.0
        temp_mask.data[~np.isnan(temp_mask.data)] = 1.0

        masked_nimrod_field = N[0:min_timesteps].copy()
        # masked_nimrod_field.data = N[0:min_timesteps].data * temp_mask[0:min_timesteps].data
        masked_nimrod_field.data *= temp_mask.data

        # Append the masked field to the output list of masked fields.
        filtered_model.append(masked_model_field)
        filtered_radar.append(masked_nimrod_field)

    # return masked_model_field and masked_nimrod_field --> these can then be passed to either
    # the histogram or time series plotting operators.

    print(" test point bmc1")
    if outputs == "Nimrod":
        filtered_fields.append(filtered_radar.merge_cube())
    print(" test point bmc2")
    if outputs == "model":
        filtered_fields.append(filtered_model.merge_cube())
    print(" test point bmc3")
    if outputs == "all":
        print(" test point bmc4")
        filtered_fields.append(filtered_model.merge_cube())
        print(" test point bmc5")
        filtered_fields.append(filtered_radar.merge_cube())

    print("+++++++++++++++++++++++++++++")
    print(filtered_fields)
    print("+++++++++++++++++++++++++++++")
    # Return either a single cube or a cubelist.
    print(" test point bmc6")
    if len(filtered_fields) == 1:
        print(" test point bmc7a")
        return filtered_fields[0]
    else:
        # return masked_fields
        # return filtered_fields.merge()
        print(" test point bmc7")
        return filtered_fields


def radar_mask_loop(
    model_field: iris.cube.Cube | iris.cube.CubeList,
    nimrod_field: iris.cube.Cube | iris.cube.CubeList,
    nimrod_mask: iris.cube.Cube | iris.cube.CubeList,
    boundary_margin: int = 8,
    outputs: str = "Nimrod",
) -> iris.cube.Cube | iris.cube.CubeList:
    """Find common domains between a list of models and radar observations."""
    # Create an empty cubelist to hold the filtered fields.
    filtered_cubes = iris.cube.CubeList([])

    # if len(nimrod_field) > 1:
    # use_nimrod_field = nimrod_field[0]
    # use_nimrod_mask = nimrod_mask[0]
    # else:
    print("-----> len(nimrod_field) ", len(nimrod_field))
    use_nimrod_field = nimrod_field
    use_nimrod_mask = nimrod_mask

    # Loop over the models.
    for model in model_field:
        print("-------> using model ", model)
        filtered_model = radar_mask(
            model,
            use_nimrod_field,
            use_nimrod_mask,
            boundary_margin=boundary_margin,
            outputs="model",
        )
        filtered_cubes.append(filtered_model)

    # Grab the filtered radar observations.
    print("-----> len(model_field) ", len(model_field))
    if len(model_field) == 1:
        filtered_radar = radar_mask(
            model_field[0],
            use_nimrod_field,
            use_nimrod_mask,
            boundary_margin=boundary_margin,
            outputs="Nimrod",
        )
    else:
        filtered_radar = radar_mask(
            model_field[0],
            use_nimrod_field,
            use_nimrod_mask,
            boundary_margin=boundary_margin,
            outputs="Nimrod",
        )

    filtered_cubes.append(filtered_radar)

    print("-----------------> returning from radar_mask_loop")
    return filtered_cubes


def match_varname_and_units(cubes: iris.cube.Cube | iris.cube.CubeList):
    """Match the varname and units of a cube list.

    Arguments
    ---------
    cubes: iris.cube.Cube | iris.cube.CubeList
        A Cube or CubeList of a field to be matched.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        The matched cubes.


    Notes
    -----
    This function converts the names and units of a cube list to match
    the first cube in the list. If just one cube is input, then this is
    returned.
    """
    # If just one cube, then no need to match so return.
    if len(cubes) == 1:
        return cubes

    print("@@@@@@@@@@@@@@@@@@@@@ base cubes[0] @@@@@@@@@@@@")
    print(cubes[0])
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

    # TODO when testing completed remove the chop [2:25] [3:46]

    # Initialise the list of matched cubes.
    new_cubelist = iris.cube.CubeList([])
    new_cubelist.append(cubes[0])
    #    new_cubelist.append(cubes[0][2:45])

    # Loop the cubes to match to the first cube.
    base_cube = cubes[0]
    print("@@@@@@@@@@@@@@@@@@@@@ base_cube @@@@@@@@@@@@")
    print("base_cube.name          : ", base_cube.name)
    print("base_cube.standard_name : ", base_cube.standard_name)
    print("base_cube.long_name     : ", base_cube.long_name)
    print("base_cube.var_name      : ", base_cube.var_name)
    print("base_cube.coords(time)  : ", base_cube.coord("time"))
    print("base_cube.coords(forecast_period) : ", base_cube.coord("forecast_period"))
    # print("------- base cube below -----------")
    # print(base_cube)
    print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
    for cube in cubes[1:]:
        print("@@@@@@@@@@@@@@@ raw @@@@@@@@@@@@@@@@@@")
        print(cube)
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
        new_cube = cube.copy()
        #        if new_cube.attributes["model_name"] == "Nimrod2km":
        #           new_cube = new_cube[3:46]
        #        else:
        #           new_cube = new_cube[2:45]

        # Match the cube varname.
        new_cube.rename(base_cube.long_name)
        new_cube.long_name = base_cube.long_name
        new_cube.var_name = base_cube.var_name

        # Match the cube units.
        new_cube.units = base_cube.units

        # Match the cube forecast_reference_time, a single value e.g. 2023-11-12 00:00:00.
        # TODO move this to the read function for radar
        forecast_reference_time_use = base_cube.coord("forecast_reference_time")
        new_cube.remove_coord("forecast_reference_time")
        new_cube.add_aux_coord(forecast_reference_time_use)
        # new_cube.replace_coord(base_cube.coord('forecast_reference_time'))

        # Match the cube forecast_period.
        # forecast_period_use = base_cube.coord('forecast_period')
        # new_cube.remove_coord("forecast_period")
        # new_cube.replace_coord(forecast_period_use, data_dims=1)

        # coord_dims = base_cube.coord_dims('forecast_period')
        # print("---> coord_dims", coord_dims)
        # dim_index = coord_dims[0] if coord_dims else 0
        # print("---> dim_index", dim_index)
        # new_coord = base_cube.coord('forecast_period')
        # print("---> new_coord", new_coord)
        # new_cube.remove_coord("forecast_period")
        # new_cube.add_dim_coord(new_coord, dim_index)

        # Match the cube forecast_period - an array points: [ 1.,  2., ..., 47., 48.].
        # TODO move this to the read function for radar
        coord_dims = base_cube.coord_dims("forecast_period")
        print("---> coord_dims", coord_dims)
        new_coord = base_cube.coord("forecast_period")
        print("---> new_coord", new_coord)
        if new_cube.coords("forecast_period"):
            new_cube.remove_coord("forecast_period")
        new_cube.add_aux_coord(new_coord, coord_dims)

        print("@@@@@@@@@@@@@@@ matched @@@@@@@@@@@@@@@@@@")
        print("new_cube.name          : ", new_cube.name)
        print("new_cube.standard_name : ", new_cube.standard_name)
        print("new_cube.long_name     : ", new_cube.long_name)
        print("new_cube.var_name      : ", new_cube.var_name)
        print("new_cube.coords(time)  : ", new_cube.coord("time"))
        print("new_cube.coords(forecast_period) : ", new_cube.coord("forecast_period"))
        print(new_cube)
        print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")

        # Append the matched cube to the output cube list.
        new_cubelist.append(new_cube)

    print(
        "---------------->bmc exiting radar_filter.match_varname_and_units len(cubes) is ",
        len(cubes),
    )
    # print(bmc_halt_this)
    return new_cubelist
