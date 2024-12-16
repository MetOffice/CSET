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

import iris
from scipy.ndimage import gaussian_filter, uniform_filter

from CSET.operators._utils import get_cube_yxcoordname


def spatial_perturbation_field(
    original_field: iris.cube.Cube,
    apply_gaussian_filter: bool = True,
    filter_scale: int = 40,
) -> iris.cube.Cube:
    """Calculate a spatial perturbation field.

    Parameters
    ----------
    original_field: iris.cube.Cube
        Iris cube containing data to smooth, supporting multiple dimensions
        (at least two spatial dimensions must be supplied, i.e. 2D).
    apply_gaussian_filter: boolean, optional
        If set to True a Gaussian filter is applied; if set to False
        a Uniform filter is applied.
        Default is True.
    filter_scale: int, optional
        Scale at which to define the filter in grid boxes. If the
        filter is a Gaussian convolution this value represents the
        standard deviation of the Gaussian kernel.
        Default is 40 grid boxes.

    Returns
    -------
    pert_field: iris.cube.Cube
        An iris cube of the spatial perturbation field.

    Notes
    -----
    In mesoscale meteorology the perturbation field is more important than the
    balanced flows for process understanding. This function is designed
    to create spatial perturbation fields based on smoothing with a Gaussian
    kernel or a uniform kernel.

    The kernels are defined by the filter_scale, which for mesoscale
    perturbations should be between an approximate cloud separation distance,
    of 30 km, and synoptic scale variations (1000 km). In practice any
    value between these ranges should provided broadly consistent results (e.g.
    [Flacketal2016]_). The Gaussian kernel will give greater importance to
    areas closer to the event and will produce a smooth perturbation field.
    The uniform kernel will produce a smooth perturbation field but will not
    give local features as much prominence.

    Caution should be applied to boundaries, particularly if the domain is of
    variable resolution, as some numerical artifacts could be introduced.

    References
    ----------
    .. [Flacketal2016] Flack, D.L.A., Plant, R.S., Gray, S.L., Lean, H.W.,
       Keil, C. and Craig, G.C. (2016) "Characterisation of Convective
       Regimes over the British Isles." Quarterly Journal of the Royal
       Meteorological Society, vol. 142, 1541-1553. doi:10.1002/qj.2758

    Examples
    --------
    >>> Temperature_perturbation = meso.spatial_perturbation_fields(Temp,
                                   gaussian_filter=True,filter_scale=40)
    >>> iplt.pcolormesh(Temperature_perturabtion[0,:,:],cmap=mpl.cm.bwr)
    >>> plt.gca().coastlines('10m')
    >>> plt.clim(-5,5)
    >>> plt.colorbar()
    >>> plt.show()

    """
    pert_field = original_field.copy()
    # find axes of spatial coordinates in field
    coords = [coord.name() for coord in original_field.coords()]
    # axes tuple containing latitude, longitude coordinate name.
    axes = (
        coords.index(get_cube_yxcoordname(original_field)[0]),
        coords.index(get_cube_yxcoordname(original_field)[1]),
    )
    # apply convolution depending on type used
    if apply_gaussian_filter:
        filter_type = "Gaussian"
        logging.info("Gaussian filter applied.")
        pert_field.data -= gaussian_filter(original_field.data, filter_scale, axes=axes)
    else:
        logging.info("Uniform filter applied.")
        filter_type = "Uniform"
        pert_field.data -= uniform_filter(original_field.data, filter_scale, axes=axes)
    # provide attributes to cube to indicate spatial perturbation field
    pert_field.attributes["perturbation_field"] = (
        f"{filter_type}_with_{str(filter_scale)}_grid_point_filter_scale"
    )
    return pert_field
