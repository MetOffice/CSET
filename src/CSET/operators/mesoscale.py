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

"""A module containing different diagnostics for mesoscales.

The diagnostics here are applicable at mesoscales and apply generally
rather than for specific aspects of mesoscale meteorology (e.g. convection).
For specific aspects, the user is referred to other modules available in
CSET.

"""

import logging
from typing import Union

import iris
import numpy as np
from scipy.ndimage import gaussian_filter, uniform_filter

from CSET._common import iter_maybe
from CSET.operators._utils import get_cube_yxcoordname


def spatial_perturbation_field(
    original_field: Union[iris.cube.Cube, iris.cube.CubeList],
    Gaussian_filter: bool = True,
    filter_scale: int = 40,
) -> Union[iris.cube.Cube, iris.cube.CubeList]:
    """Calculate a spatial perturbation field.

    Parameters
    ----------
    original_field: iris.cube.Cube | iris.cube.CubeList
        raw original field from the model
    Gaussian_filter: boolean
        Switch to determine if a Gaussian filter is applied.
        If set to True a Gaussian filter is applied; if set to False
        a Uniform filter is applied.
        Default is True.
    filter_scale: int
        Scale at which to apply the filter over in grid boxes. If the
        filter is a Gaussian convultion this value represents the
        halfwidth of the Gaussian kernel.
        Default is 40 grid points.

    Returns
    -------
    An iris cube of the spatial perturbation field, or a CubeList of the
    spatial perturbation fields in the same order they were passed into
    original_field.

    Return type
    -----------
    iris.cube.Cube | iris.cube.CubeList

    Notes
    -----
    In mesoscale meteorology the perturbation field is more important than the
    balanced flows for process understanding. This function is designed
    to create spatial perturbation fields based on smoothing with a Gaussian
    kernel or a Uniform kernel.

    The kernels are defined by the filter_scale, which for mesoscale
    perturbations should be between an approximate cloud separation distance,
    of 30 km, and synoptic scale variations (1000 km). In practice any
    value between these ranges should provided broadly consistent results (e.g.
    [Flacketal2016]_). The Gaussian kernel will give greater importance to
    areas closer to the event and will produce a smooth perturbation field.
    The Uniform kernel will produce a smooth perturbation field but will not
    give local features as much prominence.

    References
    ----------
    .. [Flacketal2016] Flack, D.L.A., Plant, R.S., Gray, S.L., Lean, H.W.,
       Keil, C. and Craig, G.C. (2016) "Characterisation of Convective
       Regimes over the British Isles." Quarterly Journal of the Royal
       Meteorological Society, vol. 142, 1541-1553. doi:10.1002/qj.2758

    Examples
    --------
    >>> Temperature_perturbation = meso.spatial_perturbation_fields(Temp,
                                   Gaussian_filter=True,filter_scale=40)
    >>> iplt.pcolormesh(Temperature_perturabtion[0,:,:],cmap=mpl.cm.bwr)
    >>> plt.gca().coastlines('10m')
    >>> plt.clim(-5,5)
    >>> plt.colorbar()
    >>> plt.show()

    """
    pert_fields = iris.cube.CubeList()
    for cube in iter_maybe(original_field):
        pert_field = cube.copy()
        # find axes of spatial coordinates in field
        coords = [coord.name() for coord in cube.coords()]
        axes = (
            coords.index(get_cube_yxcoordname(cube)[0]),
            coords.index(get_cube_yxcoordname(cube)[1]),
        )
        # apply convolution depending on type used
        if Gaussian_filter:
            filter_type = "Gaussian"
            logging.info("Gaussian filter applied.")
            half_width = np.sqrt(2 * np.log(2) * filter_scale)
            pert_field.data -= gaussian_filter(cube.data, half_width, axes=axes)
        else:
            logging.info("Uniform filter applied.")
            filter_type = "Uniform"
            pert_field.data -= uniform_filter(cube.data, filter_scale, axes=axes)
        # rename cube to indicate spatial perturbation field
        pert_field.attributes["perturbation_field"] = (
            f"{filter_type}_with_{str(filter_scale)}_grid_point_filter_scale"
        )
        pert_fields.append(pert_field)
    if len(pert_fields) == 1:
        return pert_fields[0]
    else:
        return pert_fields
