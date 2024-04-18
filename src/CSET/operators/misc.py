# Copyright 2022 Met Office and contributors.
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

from collections.abc import Iterable
from typing import Union

from iris.cube import Cube, CubeList

from CSET._common import iter_maybe


def noop(x, **kwargs):
    """Return its input without doing anything to it.

    Useful for constructing diagnostic chains.

    Arguments
    ---------
    x: Any
        Input to return.

    Returns
    -------
    x: Any
        The input that was given.
    """
    return x


def remove_attribute(
    cubes: Union[Cube, CubeList], attribute: Union[str, Iterable], **kwargs
) -> CubeList:
    """Remove a cube attribute.

    If the attribute is not on the cube, the cube is passed through unchanged.

    Arguments
    ---------
    cubes: Cube | CubeList
        One or more cubes to remove the attribute from.
    attribute: str | Iterable
        Name of attribute (or Iterable of names) to remove.

    Returns
    -------
    cubes: CubeList
        CubeList of cube(s) with the attribute removed.
    """
    # Ensure cubes is a CubeList.
    if not isinstance(cubes, CubeList):
        cubes = CubeList(iter_maybe(cubes))

    for cube in cubes:
        for attr in iter_maybe(attribute):
            cube.attributes.pop(attr, None)
    return cubes


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
    >>> field_addition = misc.addition(kinetic_energy_u, kinetic_energy_v)

    """
    return addend_1 + addend_2


def subtraction(minuend, subtrahend):
    """Subtraction of two fields.

    Parameters
    ----------
    minuend: Cube
        Any field to have another field subtracted from it.
    subtrahend: Cube
        Any field to be subtracted from to another field.

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
    creating new diagnostics by using recipes. It can be used for model
    differences to allow for comparisons between the same field in different
    models or model configurations.

    Examples
    --------
    >>> model_diff = misc.subtraction(temperature_model_A, temperature_model_B)

    """
    return minuend - subtrahend


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
    >>> bowen_ratio = misc.division(sensible_heat_flux, latent_heat_flux)

    """
    return numerator / denominator


def multiplication(multiplicand, multiplier):
    """Multiplication of two fields.

    Parameters
    ----------
    multiplicand: Cube
        Any field to be multiplied by another field.
    multiplier: Cube
        Any field to be multiplied to another field.

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
    >>> filtered_CAPE_ratio = misc.multiplication(CAPE_ratio, inflow_layer_properties)

    """
    return multiplicand * multiplier
