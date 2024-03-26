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


def addition(a, b):
    r"""Addition of two fields.

    Parameters
    ----------
    a: Cube
        Any field to have another field added to it.
    b: Cube
        Any field to be added to another field.

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
    >>> Field_addition=misc.addition(
            Kinetic_energy_u,Kinetic_energy_v)

    """
    # Add the two fields together by copying a and adding b.
    c = a.copy()
    c += b
    return c


def subtraction(a, b):
    r"""Subtraction of two fields.

    Parameters
    ----------
    a: Cube
        Any field to have another field subtracted from it.
    b: Cube
        Any field to be subtracted from to another field.

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
    creating new diagnostics by using recipes. It can be used for model
    differences to allow for comparisons between the same field in different
    models or model configurations.

    Examples
    --------
    >>> Model_difference=misc.subtraction(
            Temperature_model_A,Temperature_model_B)

    """
    # Subtract the two fields together by copying a and subtracting b.
    c = a.copy()
    c -= b
    return c


def division(a, b):
    r"""Division of two fields.

    Parameters
    ----------
    a: Cube
        Any field to have the ratio taken with respect to another field.
    b: Cube
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
    >>> Bowen_ratio=misc.division(
            sensible_heat_flux,latent_heat_flux)

    """
    # Divide the two fields together by copying a and dividing by b.
    c = a.copy()
    c /= b
    return c


def multiplication(a, b):
    r"""Multiplication of two fields.

    Parameters
    ----------
    a: Cube
        Any field to be multiplied by another field.
    b: Cube
        Any field to be multiplied to another field.

    Returns
    -------
    Cube


    Notes
    -----
    This is a simple operator designed for combination of diagnostics or
    creating new diagnostics by using recipes.

    Examples
    --------
    >>> Filtered_CAPE_ratio=misc.multiplication(
            CAPE_ratio,Inflow_layer_properties)

    """
    # Multiply the two fields together by copying a and multiplying by b.
    c = a.copy()
    c *= b
    return c
