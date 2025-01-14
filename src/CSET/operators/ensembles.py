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

"""
A module containing different diagnostics for ensembles.

The diagnostics here are applicable to ensembles and apply generally to
ensembles. They are not just limited to considering ensemble spread.
"""

import iris
import iris.cube
import numpy as np


def DKE(u: iris.cube.Cube, v: iris.cube.Cube) -> iris.cube.Cube:
    r"""Calculate the Difference Kinetic Energy (DKE).

    Parameters
    ----------
    u: iris.cube.Cube
        Iris cube of the u component of the wind field for all members. Must
        include a realization coordinate; realization must be the first
        coordinate.
    v: iris.cube.Cube
        Iris cube of the v component of the wind field same format as u.

    Returns
    -------
    DKE: iris.cube.Cube
        An iris cube of the DKE for each of the control - member comparisons.

    Notes
    -----
    The Difference Kinetic Energy, or DKE was first used in an ensemble sense
    by [Zhangetal2002]_. It is calculated as

    .. math:: \frac{1}{2}u'u' + \frac{1}{2}v'v'

    where

    .. math:: x' = x_{control} - x_{perturbed}

    for each member of the ensemble.

    The DKE is used to show links between the perturbation growth (growth of
    ensemble spread) or errors with dynamical features. It can be particularly
    useful in understanding differences in physical mechanisms between ensemble
    members. The larger the DKE the greater the difference between the two
    members being considered.

    The DKE can be viewed as a domain average, horizontal integration (to
    produce profiles), or vertical integration/subsampling (to provide spatial maps).
    Furthermore, weightings based on volume or mass can be applied to these
    integrations. However, initially the DKE per unit mass is implemented here.

    The DKE is often considered in the form of power spectra to identify the
    presence of upscale error growth or the dominant scales of error growth. It
    is often plotted on a logarithmic scale.

    References
    ----------
    .. [Zhangetal2002] Zhang, F., Snyder, C., and Rotunno, R., (2002)
       "Mesoscale Predictability of the 'Surprise' Snowstorm of 24-25 January
       2000." Monthly Weather Review, vol. 130, 1617-1632,
       doi: 10.1175/1520-0493(2002)130<1617:MPOTSS>2.0.CO;2

    Examples
    --------
    >>> DKE = ensembles.DKE(u, v)
    """
    for cube in [u, v]:
        # Use dim_map to store the dimensions and check the realization
        # coordinate is the first coordinate.
        dim_map = {}
        for coord in cube.dim_coords:
            dim_index = cube.coord_dims(coord.name())[0]
            dim_map[coord.name()] = dim_index
        if "realization" not in dim_map:
            raise ValueError("Cube should have a realization coordinate.")
        if not dim_map["realization"] == 0:
            raise ValueError("Realization should be the first coordinate in cube.")

    # Check cubes are the same shape.
    if u.shape != v.shape:
        raise ValueError("Cubes should be the same shape.")

    # Check coordinates are identical.
    for coord_u, coord_v in zip(u.dim_coords, v.dim_coords, strict=True):
        if not u.coord(coord_u.name()) == v.coord(coord_v.name()):
            raise ValueError(
                f"u and v should have matching coordinates for {coord_u.name()}."
            )
    # Define control member and perturbed members.
    u_ctrl = u[np.where(u.coord("realization").points[:] == 0)[0][0], :]
    u_mem = u[np.where(u.coord("realization").points[:] != 0)[0][:], :]
    v_ctrl = v[np.where(v.coord("realization").points[:] == 0)[0][0], :]
    v_mem = v[np.where(v.coord("realization").points[:] != 0)[0][:], :]

    # Calculate the DKE
    DKE = u_mem.copy()
    DKE.data[:] = 0.0
    DKE.data = (
        0.5 * (u_ctrl.data - u_mem.data) ** 2 + 0.5 * (v_ctrl.data - v_mem.data) ** 2
    )
    DKE.rename("Difference Kinetic Energy")
    return DKE
