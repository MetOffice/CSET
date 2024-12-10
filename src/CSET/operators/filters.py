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

from typing import Union

import iris
import iris.cube
import iris.exceptions
import numpy as np

from CSET._common import iter_maybe


def apply_mask(
    original_field: Union[iris.cube.Cube, iris.cube.CubeList],
    masks: Union[iris.cube.Cube, iris.cube.CubeList],
) -> Union[iris.cube.Cube, iris.cube.CubeList]:
    """Apply a mask to given data as a masked array.

    Parameters
    ----------
    original_field: iris.cube.Cube | iris.cube.CubeList
        The field to be masked.
    masks: iris.cube.Cube | iris.cube.CubeList
        The mask being applied to the original field.

    Returns
    -------
    A masked field.

    Return type
    -----------
    iris.cube.Cube | iris.cube.CubeList

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
    mask_list = iris.cube.CubeList()
    for mask in iter_maybe(masks):
        mask.data[mask.data == 0] = np.nan
        mask_list.append(mask)
    if len(mask_list) == 1:
        masked_field = original_field.copy()
        masked_field.data *= mask_list[0].data
        masked_field.rename(f"mask_of_{original_field.name()}")
        return masked_field
    else:
        mask_field_list = iris.cube.CubeList()
        for data, mask in zip(original_field, mask_list, strict=True):
            mask_field_data = data.copy()
            mask_field_data.data *= mask.data
            mask_field_data.rename(f"mask_of_{data.name()}")
            mask_field_list.append(mask_field_data)
        return mask_field_list


def filter_cubes(
    cube: Union[iris.cube.Cube, iris.cube.CubeList],
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
    cubes: Union[iris.cube.Cube, iris.cube.CubeList],
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
    mask_field: Union[iris.cube.Cube, iris.cube.CubeList],
    condition: str,
    value: float,
) -> Union[iris.cube.Cube, iris.cube.CubeList]:
    """Generate a mask to remove data not meeting conditions.

    Parameters
    ----------
    mask_field: iris.cube.Cube | iris.cube.CubeList
        The field to be used for creating the mask.
    condition: str
        The type of condition applied, six available options:
        '==','!=','<','<=','>', and '>='.
    value: float
        The value on the other side of the condition.

    Returns
    -------
    Masks meeting the conditions applied.

    Return type
    -----------
    iris.cube.Cube | iris.cube.CubeList

    Raises
    ------
    ValueError: Unexpected value for condition. Expected ==, !=, >, >=, <, <=
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

    The same condition and value will be used when masking multiple cubes.

    Examples
    --------
    >>> land_mask = generate_mask(land_sea_mask,'==',1)
    """
    mask_list = iris.cube.CubeList()
    for cube in iter_maybe(mask_field):
        masks = cube.copy()
        masks.data = np.zeros(masks.data.shape)
        if condition == "==":
            masks.data[cube.data == value] = 1
        elif condition == "!=":
            masks.data[cube.data != value] = 1
        elif condition == ">":
            masks.data[cube.data > value] = 1
        elif condition == ">=":
            masks.data[cube.data >= value] = 1
        elif condition == "<":
            masks.data[cube.data < value] = 1
        elif condition == "<=":
            masks.data[cube.data <= value] = 1
        else:
            raise ValueError("""Unexpected value for condition. Expected ==, !=,
                              >, >=, <, <=""")
        masks.rename(f"mask_for_{cube.name()}_{condition}_{value}")
        masks.attributes.pop("STASH", None)

        mask_list.append(masks)
    if len(mask_list) == 1:
        return mask_list[0]
    else:
        return mask_list
