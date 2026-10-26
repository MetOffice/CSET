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

"""Vorticity operators."""

import iris
import iris.analysis.calculus
from iris.cube import Cube, CubeList

from CSET._common import iter_maybe


def relative_vorticity(
    u_cube: Cube | CubeList,
    v_cube: Cube | CubeList,
    w_cube: Cube | CubeList | None = None,
) -> Cube | CubeList:
    """Calculate the relative vorticity of a cube from wind components.

    Arguments
    ---------
    u_cube: iris.cube.Cube | iris.cube.CubeList
        A Cube or CubeList of the zonal component of the wind.

    v_cube: iris.cube.Cube | iris.cube.CubeList
        A Cube or CubeList of the meridional component of the wind.

    w_cube: iris.cube.Cube | iris.cube.CubeList | None
        An optional argument, default is None. A Cube or CubeList
        of the vertical component of the wind. If included the three
        components of vorticity are calculated, otherwise the vertical
        component of vorticity is calculated.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        The relative vorticity as either one or three dimensions depending
        upon if two or three components of winds are given.

    Notes
    -----
    The relative vorticity is calculated as the curl of the wind. It automatically
    determines if the spherical curl or cartesian curl is calculated based
    on the cubes coordinate system. In essence this operator is a CSET wrapper around
    `iris.analysis.calculus.curl <https://scitools-iris.readthedocs.io/en/stable/generated/api/iris.analysis.calculus.html#iris.analysis.calculus.curl>`_ adapted for wind.

    It's interpretation depends on the hemisphere you are in. Southern
    hemispheric convections are opposite to Northern hemispheric convections.
    In the Northern hemisphere negative vorticity implies cyclonic circulation
    whereas, positive vorticity implies anticyclonic circulation (e.g. [Holton13]_).

    If all three wind components are given a cube list will be created.
    It is recommended to use a filter step within the recipe to get the
    correct component depending upon your usage.

    Examples
    --------
    >>> Zeta = vorticity.relative_vorticity(u_cube, v_cube)
    >>> 3D_vorticity = vorticity.relative_vorticity(u_cube, v_cube, w_cube)
    """
    new_cubelist = CubeList([])
    if w_cube == None:
        for u, v in zip(iter_maybe(u_cube), iter_maybe(v_cube), strict=True):
            _, _, zeta = iris.analysis.calculus.curl(u, v, None)
            zeta.rename("vertical_component_of_relative_vorticity")
            new_cubelist.append(zeta)
        if len(new_cubelist) == 1:
            return new_cubelist[0]
        else:
            return new_cubelist
    else:
        for u, v, w in zip(
            iter_maybe(u_cube), iter_maybe(v_cube), iter_maybe(w_cube), strict=True
        ):
            xi, eta, zeta = iris.analysis.calculus.curl(u, v, w)
            xi.rename("zonal_component_of_relative_vorticity")
            eta.rename("meridional_component_of_relative_vorticity")
            zeta.rename("vertical_component_of_relative_vorticity")
            new_cubelist.append([xi, eta, zeta])
        return new_cubelist
