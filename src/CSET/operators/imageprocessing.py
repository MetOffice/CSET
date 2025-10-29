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

"""Operators to perform various kinds of image processing."""

import logging

import iris
import iris.cube
import numpy as np
from skimage.metrics import structural_similarity

from CSET.operators._utils import fully_equalise_attributes, get_cube_yxcoordname
from CSET.operators.misc import _extract_common_time_points
from CSET.operators.regrid import regrid_onto_cube


def structural_similarity_model_comparisons(
    cubes: iris.cube.CubeList, sigma: float = 1.5, spatial_plot: bool = False
) -> iris.cube.Cube:
    r"""Calculate the structural similarity and produces a spatial plot or timeseries.

    Parameters
    ----------
    cubes: iris.cube.CubeList
        A list of exactly two cubes. One must have the cset_comparison_base
        attribute set to 1, and will be used as the base of the comparison.
        The cubes must contain a time coordinate.
    sigma: float, optional
        The standard deviation of the Gaussian kernel to be used. The default
        is set to 1.5 to mimic the human eye following [Wangetal2004]_.
    spatial_plot: bool, optional
        If set to True a 2D field of the structural similarity will be output;
        if set to False a 1D field of the mean structural similarity is output.
        Default is False.

    Returns
    -------
    iris.cube.Cube

    Raises
    ------
    ValueError
        When the cubes are not compatible, or no time coordinate.

    Notes
    -----
    This diagnostic was introduced by Wang et al. (2004) [Wangetal2004]_. It is
    an image processing diagnostic that takes into account three factors asscoiated
    with an image: i) luminace, ii) contrast, iii) structure. In calculation terms
    it is a combination of the intensity, variance, and co-variance of an image. It is
    calculated as follows:

    .. math:: SSIM(x,y) = \frac{(2\mu_{x}\mu_{y} + C_{1})(2\sigma_{xy} + C_{2})}{(\mu^{2}_{x}\mu^{2}_{y} + C_{1})(\sigma^{2}_{x}\sigma^{2}_{y} + C_{2})}

    for images, x and y, and small constancts C1 and C2, with the other symbols having
    their usual statistical meaning.

    The diagnostic varies between positive and negative one, on the most part.
    However, should the data being compared lie outside of the specified data
    range values larger or smaller can occur. Values close to or exactly 1 imply
    a perceptably similar image; values close to or exactly -1 imply an anticorrelated
    image; small values imply the fields are perceptably different.

    The diagnostic has been setup with default values that are designed to mimic the
    human eye and so are universally applicable irrespective of model resolution.
    However, it should be noted that the mean structural similarity is not
    identical to the domain mean of the structural similarity. This difference
    occurs because the former is calculated over the mean of all the windows
    (Gaussian kernels) rather than the mean of the grid boxes.

    Further details, including caveats, can be found in Wang et al. (2004)
    [Wangetal2004]_.

    References
    ----------
    .. [Wangetal2004] Wang, Z., Bovik, A.C., Sheikh, H.R., Simoncelli, E.P. (2004)
       "Image Quality Assessment: From Error Visibility to Structural Similarity."
       IEEE Transactions on Image Processing, vol. 13, 600-612,
       doi: 10.1109/TIP.2003.819861

    Examples
    --------
    >>> MSSIM = imageprocessing.structural_similarity_model_comparisons(
            cubes,sigma=1.5, spatial_plot=False)
    >>> iplt.plot(MSSIM)

    >>> SSIM = imageprocessing.structural_similarity_model_comparisons(
            cubes, sigma=1.5, spatial_plot=True)
    >>> iplt.pcolormesh(SSIM[0,:], cmap=mpl.cm.bwr)
    >>> plt.gca().coastlines('10m')
    >>> plt.clim(-1, 1)
    >>> plt.colorbar()
    >>> plt.show()
    """
    if len(cubes) != 2:
        raise ValueError("cubes should contain exactly 2 cubes.")
    base: iris.cube.Cube = cubes.extract_cube(
        iris.AttributeConstraint(cset_comparison_base=1)
    )
    other: iris.cube.Cube = cubes.extract_cube(
        iris.Constraint(
            cube_func=lambda cube: "cset_comparison_base" not in cube.attributes
        )
    )

    # Get spatial coord names.
    base_lat_name, base_lon_name = get_cube_yxcoordname(base)
    other_lat_name, other_lon_name = get_cube_yxcoordname(other)

    # Ensure cubes to compare are on common differencing grid.
    # This is triggered if either
    #      i) latitude and longitude shapes are not the same. Note grid points
    #         are not compared directly as these can differ through rounding
    #         errors.
    #     ii) or variables are known to often sit on different grid staggering
    #         in different models (e.g. cell center vs cell edge), as is the case
    #         for UM and LFRic comparisons.
    # In future greater choice of regridding method might be applied depending
    # on variable type. Linear regridding can in general be appropriate for smooth
    # variables. Care should be taken with interpretation of differences
    # given this dependency on regridding.
    if (
        base.coord(base_lat_name).shape != other.coord(other_lat_name).shape
        or base.coord(base_lon_name).shape != other.coord(other_lon_name).shape
    ) or (
        base.long_name
        in [
            "eastward_wind_at_10m",
            "northward_wind_at_10m",
            "northward_wind_at_cell_centres",
            "eastward_wind_at_cell_centres",
            "zonal_wind_at_pressure_levels",
            "meridional_wind_at_pressure_levels",
            "potential_vorticity_at_pressure_levels",
            "vapour_specific_humidity_at_pressure_levels_for_climate_averaging",
        ]
    ):
        logging.debug(
            "Linear regridding base cube to other grid to compute differences"
        )
        base = regrid_onto_cube(base, other, method="Linear")

    def is_increasing(sequence: list) -> bool:
        """Determine the direction of an ordered sequence.

        Returns a boolean indicating that the values of a sequence are
        increasing. The sequence should already be monotonic, with no
        duplicate values. An iris DimCoord's points fulfils this criteria.
        """
        return sequence[0] < sequence[1]

    # Figure out if we are comparing between UM and LFRic; flip array if so.
    base_lat_direction = is_increasing(base.coord(base_lat_name).points)
    other_lat_direction = is_increasing(other.coord(other_lat_name).points)
    if base_lat_direction != other_lat_direction:
        other.data = np.flip(other.data, other.coord(other_lat_name).cube_dims(other))

    # Extract just common time points.
    base, other = _extract_common_time_points(base, other)

    # Equalise attributes so we can merge.
    fully_equalise_attributes([base, other])
    logging.debug("Base: %s\nOther: %s", base, other)

    # Get the name of the first non-scalar time coordinate.
    time_coord = next(
        map(
            lambda coord: coord.name(),
            filter(
                lambda coord: coord.shape > (1,) and coord.name() in ["time", "hour"],
                base.coords(),
            ),
        ),
        None,
    )

    if time_coord is None:
        raise ValueError("Cubes should contain a time coordinate.")
    # Create and empty CubeList for storing the time or realization data.
    ssim = iris.cube.CubeList()

    # Use boolean input to determine if a spatial plot is being output or the mean SSIM.
    if not spatial_plot:
        # Loop over realization and time coordinates.
        for base_r, other_r in zip(
            base.slices_over("realization"),
            other.slices_over("realization"),
            strict=True,
        ):
            if time_coord == "hour":
                for base_t, other_t in zip(
                    base_r.slices_over("hour"), other_r.slices_over("hour"), strict=True
                ):
                    # The MSSIM (Mean structural similarity) is compression to
                    # a single point. Therefore, copying cube data for one
                    # point in the domain to keep cube consistency.
                    mssim = base_t[0, 0].copy()
                    mssim.data = structural_similarity(
                        base_t.data,
                        other_t.data,
                        data_range=other_t.data.max() - other_t.data.min(),
                        gaussian_weights=True,
                        sigma=sigma,
                    )
                    ssim.append(mssim)
            else:
                logging.debug("Assume time_coord is 'time'.")
                for base_t, other_t in zip(
                    base_r.slices_over("time"), other_r.slices_over("time"), strict=True
                ):
                    # The MSSIM (Mean structural similarity) is compression to
                    # a single point. Therefore, copying cube data for one
                    # point in the domain to keep cube consistency.
                    mssim = base_t[0, 0].copy()
                    mssim.data = structural_similarity(
                        base_t.data,
                        other_t.data,
                        data_range=other_t.data.max() - other_t.data.min(),
                        gaussian_weights=True,
                        sigma=sigma,
                    )
                    ssim.append(mssim)
    else:
        # Loop over realization and time coordinates.
        for base_r, other_r in zip(
            base.slices_over("realization"),
            other.slices_over("realization"),
            strict=True,
        ):
            for base_t, other_t in zip(
                base_r.slices_over(time_coord), other_r.slices_over(time_coord), strict=True
            ):
                # Use the full array as output will be as a 2D map.
                ssim_map = base_t.copy()
                _, ssim_map.data = structural_similarity(
                    base_t.data,
                    other_t.data,
                    data_range=other_t.data.max() - other_t.data.min(),
                    gaussian_weights=True,
                    sigma=sigma,
                    full=True,
                )
                ssim.append(ssim_map)
    # Merge the cube slices into one cube, rename, and change units.
    ssim = ssim.merge_cube()
    ssim.standard_name = None
    ssim.long_name = "structural_similarity"
    ssim.units = "1"
    return ssim
