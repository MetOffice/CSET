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

"""
Example operators to show what they should look like, especially around
documentation.

Currently the operators are just functions, but we may instead want to use
callable classes so they can have some setup done, or perhaps have some state
(though state is something we want to minimise).
"""


def example_increment_operator(n: float, **kwargs) -> float:
    """
    Increments the input by one.

    Parameters
    ----------
    n: int or float
        The starting number which is incremented.

    Returns
    -------
    int or float
        The result of adding one.

    Raises
    ------
    TypeError
        If n is not a number.

    Notes
    -----
    This is a simple function to demonstrate how they should be generally
    written. It implements addition. [1]_

    The operation of this function is described by the following equation:

    .. math:: n_{final} = n_{initial} + \\int^{1}_{0} \\frac{x}{1} dx

    References
    ----------
    .. [1] Wikipedia contributors, "Addition," Wikipedia, The Free Encyclopedia,
        https://en.wikipedia.org/w/index.php?title=Addition&oldid=1112352709

    Examples
    --------
    >>> Example.example.example_increment_operator(3)
    4
    """
    return n + 1


def example_decrement_operator(n: float, **kwargs) -> float:
    """
    Decreases the input by one.

    Parameters
    ----------
    n: int or float
        The starting number which is decremented.

    Returns
    -------
    int or float
        The result of subtracting one.

    Raises
    ------
    TypeError
        If n is not a number.

    Notes
    -----
    This is a simple function to demonstrate how they should be generally
    written. It implements subtraction. [2]_

    The operation of this function is described by the following equation:

    .. math:: n_{final} = n_{initial} - \\int^{1}_{0} \\frac{x}{1} dx

    References
    ----------
    .. [2] Wikipedia contributors, "Subtraction," Wikipedia, The Free Encyclopedia,
        https://en.wikipedia.org/w/index.php?title=Subtraction&oldid=1121909623

    Examples
    --------
    >>> Example.example.example_decrement_operator(3)
    2
    """
    return n - 1
