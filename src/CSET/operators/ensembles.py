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

"""
A module containing different diagnostics for ensembles.

The diagnostics here are applicable to ensembles and apply generally to
ensembles. They are not just limited to considering ensemble spread.
"""

import iris


def DKE(
    u: iris.cube.Cube,
    v: iris.cube.Cube,
) -> iris.cube.Cube:
    r"""Calculate the Difference Kinetic Energy (DKE).

    Parameters
    ----------
    u: iris.cube.Cube
        Iris cube of the u component of the wind field for all members. Must be
        a minimum of three dimensions: realization, latitude, longitude.
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

    The DKE is used to show links between the peturbation growth (growth of
    enesemble spread) or errors with dynamical features. It can be particularly
    useful in understanding differences in physical mechanisms between ensemble
    members. The larger the DKE the greater the difference between the two
    members being considered.

    The DKE can be viewed as a domain average, horizontal integration (to
    produce profiles), or vertical integration (to provide spatial maps).
    Furthermore, weigthings based on volume or mass can be applied to these
    integrations. However, initially the DKE per unit mass is implemented here.

    The DKE is often considered in the form  of power spectra to identify the
    presence of upscale error growth or the dominant scales of error growth.

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
    # Check dimensionality and coordinates of the cubes are identical.
    if not u._ndim >= 3:
        raise ValueError(f"Cube expected to be 3D. Got {u.ndim}.")
    if not u.shape == v.shape:
        raise ValueError("Cubes are not the same shape")
    if not u.coord == v.coord:
        raise ValueError("u and v are on different coordinates")

    # Define control member and perturbed members.
    u_ctrl = u[0, :, :, :]
    u_mem = u[1:, :, :, :]
    v_ctrl = v[0, :, :, :]
    v_mem = v[1:, :, :, :]

    # Calculate the DKE
    DKE = u_mem.copy()
    DKE.data = (
        0.5 * (u_ctrl.data - u_mem.data) ** 2 + 0.5 * (v_ctrl.data - v_mem.data) ** 2
    )
    DKE.rename("Difference Kinetic Energy")
    return DKE
