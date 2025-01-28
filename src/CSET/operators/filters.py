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

"""Operators to perform various kind of filtering."""

import logging

import iris
import iris.cube
import iris.exceptions
import numpy as np


def apply_mask(
    original_field: iris.cube.Cube,
    mask: iris.cube.Cube,
) -> iris.cube.Cube:
    """Apply a mask to given data as a masked array.

    Parameters
    ----------
    original_field: iris.cube.Cube
        The field to be masked.
    mask: iris.cube.Cube
        The mask being applied to the original field.

    Returns
    -------
    masked_field: iris.cube.Cube
        A cube of the masked field.

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
    # Ensure mask is only 1s or NaNs.
    mask.data[mask.data == 0] = np.nan
    mask.data[~np.isnan(mask.data)] = 1
    logging.info(
        "Mask set to 1 or 0s, if addition of multiple masks results"
        "in values > 1 these are set to 1."
    )
    masked_field = original_field.copy()
    masked_field.data *= mask.data
    masked_field.attributes["mask"] = f"mask_of_{original_field.name()}"
    return masked_field


def filter_cubes(
    cube: iris.cube.Cube | iris.cube.CubeList,
    constraint: iris.Constraint,
    **kwargs,
) -> iris.cube.Cube:
    """Filter a CubeList down to a single Cube based on a constraint.

    Arguments
    ---------
    cube: iris.cube.Cube | iris.cube.CubeList
        Cube(s) to filter
    constraint: iris.Constraint
        Constraint to extract

    Returns
    -------
    iris.cube.Cube

    Raises
    ------
    ValueError
        If the constraint doesn't produce a single cube.
    """
    filtered_cubes = cube.extract(constraint)
    # Return directly if already a cube.
    if isinstance(filtered_cubes, iris.cube.Cube):
        return filtered_cubes
    # Check filtered cubes is a CubeList containing one cube.
    if isinstance(filtered_cubes, iris.cube.CubeList) and len(filtered_cubes) == 1:
        return filtered_cubes[0]
    else:
        raise ValueError(
            f"Constraint doesn't produce single cube. Constraint: {constraint}"
            f"\nSource: {cube}\nResult: {filtered_cubes}"
        )


def filter_multiple_cubes(
    cubes: iris.cube.Cube | iris.cube.CubeList,
    **kwargs,
) -> iris.cube.CubeList:
    """Filter a CubeList on multiple constraints, returning another CubeList.

    Arguments
    ---------
    cube: iris.cube.Cube | iris.cube.CubeList
        Cube(s) to filter
    constraint: iris.Constraint
        Constraint to extract. This must be a named argument. There can be any
        number of additional constraints, they just need unique names.

    Returns
    -------
    iris.cube.CubeList

    Raises
    ------
    ValueError
        The constraints don't produce a single cube per constraint.
    """
    # Ensure input is a CubeList.
    if isinstance(cubes, iris.cube.Cube):
        cubes = iris.cube.CubeList((cubes,))
    if len(kwargs) < 1:
        raise ValueError("Must have at least one constraint.")
    try:
        filtered_cubes = cubes.extract_cubes(kwargs.values())
    except iris.exceptions.ConstraintMismatchError as err:
        raise ValueError(
            "The constraints don't produce a single cube per constraint."
        ) from err
    return filtered_cubes


def generate_mask(
    mask_field: iris.cube.Cube,
    condition: str,
    value: float,
) -> iris.cube.Cube:
    """Generate a mask to remove data not meeting conditions.

    Parameters
    ----------
    mask_field: iris.cube.Cube
        The field to be used for creating the mask.
    condition: str
        The type of condition applied, six available options:
        '==','!=','<','<=','>', and '>='.
    value: float
        The value on the right hand side of the condition.

    Returns
    -------
    mask: iris.cube.Cube
        Mask meeting the condition applied.

    Raises
    ------
    ValueError: Unexpected value for condition. Expected ==, !=, >, >=, <, <=.
                Got {condition}.
        Raised when condition is not supported.

    Notes
    -----
    The mask is created in the opposite sense to numpy.ma.masked_arrays. This
    method was chosen to allow easy combination of masks together outside of
    this function using misc.addition or misc.multiplication depending on
    applicability. The combinations can be of any fields such as orography >
    500 m, and humidity == 100 %.

    The conversion to a masked array occurs in the apply_mask routine, which
    should happen after all relevant masks have been combined.

    Examples
    --------
    >>> land_mask = generate_mask(land_sea_mask,'==',1)
    """
    mask = mask_field.copy()
    mask.data = np.zeros(mask.data.shape)
    match condition:
        case "==":
            mask.data[mask_field.data == value] = 1
        case "!=":
            mask.data[mask_field.data != value] = 1
        case ">":
            mask.data[mask_field.data > value] = 1
        case ">=":
            mask.data[mask_field.data >= value] = 1
        case "<":
            mask.data[mask_field.data < value] = 1
        case "<=":
            mask.data[mask_field.data <= value] = 1
        case _:
            raise ValueError("""Unexpected value for condition. Expected ==, !=,
                              >, >=, <, <=. Got {condition}.""")
    mask.attributes["mask"] = f"mask_for_{mask_field.name()}_{condition}_{value}"
    return mask
