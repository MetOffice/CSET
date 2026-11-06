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

"""Miscellaneous operators."""

import logging

import iris
import iris.analysis.calculus
import numpy as np
from iris.cube import Cube, CubeList

from CSET._common import iter_maybe

logger = logging.getLogger(__name__)


def addition(addend_1, addend_2):
    """Addition of two fields.

    Parameters
    ----------
    addend_1: Cube
        Any field to have another field added to it.
    addend_2: Cube
        Any field to be added to another field.

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
    >>> field_addition = maths.addition(kinetic_energy_u, kinetic_energy_v)

    """
    return addend_1 + addend_2


def subtraction(
    minuend: Cube | CubeList, subtrahend: Cube | CubeList
) -> Cube | CubeList:
    """Subtraction of two fields.

    Parameters
    ----------
    minuend: Cube | CubeList
        Any field(s) to have another field subtracted from it.
    subtrahend: Cube | CubeList
        Any field(s) to be subtracted from to another field.

    Returns
    -------
    Cube | CubeList

    Raises
    ------
    ValueError, iris.exceptions.NotYetImplementedError
        When the cubes are not compatible.

    Notes
    -----
    This is a simple operator designed for combination of diagnostics or
    creating new diagnostics by using recipes. It can be used for model
    differences to allow for comparisons between the same field in different
    models or model configurations.

    If called with 2 Cubes as input, will return a difference cube.
    If called with 2 CubeLists as input, with return a CubeList of differences.
    If called with CubeList as minuend and Cube as subtrahend, will return CubeList of differences subtracting Cube from each element of input CubeList.
    If called with Cube as minuend and CubeList as subtrahend, will return CubeList of differences subtracting each element on CubeList from input Cube.

    Examples
    --------
    >>> model_diff = maths.subtraction(temperature_model_A, temperature_model_B)

    """

    def subtract_preserve_attributes(cube_a: Cube, cube_b: Cube) -> Cube:
        result = cube_a - cube_b
        result.attributes.update(cube_a.attributes)
        return result

    # Case where both inputs are single cubes
    if isinstance(minuend, iris.cube.Cube) and isinstance(subtrahend, iris.cube.Cube):
        return subtract_preserve_attributes(minuend, subtrahend)

    # Check if minuend is iterable
    cubes_a = iter_maybe(minuend)

    # Case: subtrahend also iterable
    if isinstance(subtrahend, iris.cube.CubeList):
        cubes_b = iter_maybe(subtrahend)
        if isinstance(minuend, iris.cube.CubeList):
            # Case: subtract cubelist from cubelist - assume both same sizes
            result = iris.cube.CubeList(
                [
                    subtract_preserve_attributes(cube_a, cube_b)
                    for cube_a, cube_b in zip(cubes_a, cubes_b, strict=True)
                ]
            )
        else:
            # Case: subtract each element of subtrahend from single cube
            result = iris.cube.CubeList(
                [subtract_preserve_attributes(minuend, cube_b) for cube_b in cubes_b]
            )
    else:
        # Case: subtract single cube from each minuend
        result = iris.cube.CubeList(
            [subtract_preserve_attributes(cube_a, subtrahend) for cube_a in cubes_a]
        )

    # Return single cube if only one result, else return CubeList
    return result[0] if len(result) == 1 else result


def division(numerator, denominator):
    """Division of two fields.

    Parameters
    ----------
    numerator: Cube
        Any field to have the ratio taken with respect to another field.
    denominator: Cube
        Any field used to divide another field or provide the reference
        value in a ratio.

    Returns
    -------
    Cube

    Raises
    ------
    ValueError
        When the cubes are not compatible.

    Notes
    -----
    This is a simple operator designed for combination of diagnostics or
    creating new diagnostics by using recipes.

    Examples
    --------
    >>> bowen_ratio = maths.division(sensible_heat_flux, latent_heat_flux)

    """
    return numerator / denominator


def multiplication(
    multiplicand: Cube | CubeList, multiplier: Cube | CubeList
) -> Cube | CubeList:
    """Multiplication of two fields.

    Parameters
    ----------
    multiplicand: Cube | CubeList
        Any field to be multiplied by another field.
    multiplier: Cube | CubeList
        Any field to be multiplied to another field.

    Returns
    -------
    Cube | CubeList
        The result of multiplicand x multiplier.

    Raises
    ------
    ValueError
        When the cubes are not compatible.

    Notes
    -----
    This is a simple operator designed for combination of diagnostics or
    creating new diagnostics by using recipes. CubeLists are multiplied
    on a strict ordering (e.g. first cube with first cube).

    Examples
    --------
    >>> filtered_CAPE_ratio = maths.multiplication(CAPE_ratio, inflow_layer_properties)

    """
    new_cubelist = iris.cube.CubeList([])
    for cube_a, cube_b in zip(
        iter_maybe(multiplicand), iter_maybe(multiplier), strict=True
    ):
        multiplied_cube = cube_a * cube_b
        multiplied_cube.rename(f"{cube_a.name()}_x_{cube_b.name()}")
        new_cubelist.append(multiplied_cube)
    if len(new_cubelist) == 1:
        return new_cubelist[0]
    else:
        return new_cubelist


def differentiate(
    cubes: iris.cube.Cube | iris.cube.CubeList, coordinate: str, **kwargs
) -> iris.cube.Cube | iris.cube.CubeList:
    """Differentiate a cube on a specified coordinate.

    Arguments
    ---------
    cubes: iris.cube.Cube | iris.cube.CubeList
        A Cube or CubeList of a field that is to be differentiated.

    coordinate: str
        The coordinate that is to be differentiated over.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        The differential of the cube along the specified coordinate.

    Notes
    -----
    The differential is calculated based on a carteisan grid. This calculation
    is then suitable for vertical and temporal derivatives. It is not sensible
    for horizontal derivatives if they are based on spherical coordinates (e.g.
    latitude and longitude). In essence this operator is a CSET wrapper around
    `iris.analysis.calculus.differentiate <https://scitools-iris.readthedocs.io/en/stable/generated/api/iris.analysis.calculus.html#iris.analysis.calculus.differentiate>`_.

    Examples
    --------
    >>> dT_dz = maths.differentiate(temperature, "altitude")
    """
    new_cubelist = iris.cube.CubeList([])
    for cube in iter_maybe(cubes):
        dcube = iris.analysis.calculus.differentiate(cube, coordinate)
        new_cubelist.append(dcube)
    if len(new_cubelist) == 1:
        return new_cubelist[0]
    else:
        return new_cubelist


def round_data(cubes: Cube | CubeList, decimals: int) -> Cube | CubeList:
    """Round data in a cube or cubelist to a specified number of decimal places.

    Parameters
    ----------
    cubes : Cube | CubeList
        A Cube or CubeList of fields to be rounded.
    decimals : int
        The number of decimal places to round to.

    Returns
    -------
    Cube | CubeList
        The rounded cube, or a CubeList of rounded cubes if more than one
        cube was given.
    """
    if not isinstance(decimals, int) or isinstance(decimals, bool):
        raise TypeError(
            f"decimals must be an integer, got {type(decimals).__name__}: {decimals!r}"
        )

    rounded_cubes = CubeList()
    for cube in iter_maybe(cubes):
        rounded_cube = cube.copy()
        rounded_cube.data = np.round(rounded_cube.core_data(), decimals)
        rounded_cubes.append(rounded_cube)

    return rounded_cubes[0] if len(rounded_cubes) == 1 else rounded_cubes
