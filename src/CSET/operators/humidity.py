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

"""Operators for humidity conversions."""

import iris.cube
import numpy as np

from CSET._common import iter_maybe
from CSET.operators._atmospheric_constants import EPSILON
from CSET.operators._utils import get_cube_coordindex
from CSET.operators.misc import convert_units
from CSET.operators.pressure import vapour_pressure


def mixing_ratio_from_specific_humidity(
    specific_humidity: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Convert specific humidity to mixing ratio.

    Arguments
    ---------
    specific_humidity: iris.cube.Cube | iris.cube.CubeList
        Cubes of specific humidity to be converted to mixing ratio.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Converted mixing ratio.

    Notes
    -----
    Atmospheric water vapour can be described by multiple quantities. Here,
    we convert the specific humidity to the mixing ratio using the following
    relation

    .. math:: w = \frac{q}{1 - q}

    with w the mixing ratio and q the specific humidity.

    Larger mixing ratios imply more moisture in the atmosphere. The mixing
    ratio will have the same units as the specific humidity (kg/kg).


    Examples
    --------
    >>> w = humidity.mixing_ratio_from_specific_humidity(specific_humidity)
    """
    w = iris.cube.CubeList([])
    for q in iter_maybe(specific_humidity):
        mr = q.copy()
        mr = q / (1 - q)
        mr.rename("mixing_ratio")
        w.append(mr)
    if len(w) == 1:
        return w[0]
    else:
        return w


def specific_humidity_from_mixing_ratio(
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Convert mixing ratio to specific humidity.

    Arguments
    ---------
    mixing_ratio: iris.cube.Cube | iris.Cube.CubeList
        Cubes of mixing ratio to be converted to specific humidity.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Converted specific humidity.

    Notes
    -----
    Here, we invert the relationship from `humidity.mixing_ratio_from_specific_humidity`
    for the following relation

    .. math:: q = \frac{w}{1 + w}

    with q the specific humidity and w the mixing ratio.

    A larger specific humidity implies a more moist atmosphere. The specific
    humidity will have the same units as the mixing ratio (kg/kg).

    Examples
    --------
    >>> q = humidity.specific_humidity_from_mixing_ratio(mixing_ratio)
    """
    q = iris.cube.CubeList([])
    for w in iter_maybe(mixing_ratio):
        sh = w.copy()
        sh = w / (1 + w)
        sh.rename("specific_humidity")
        q.append(sh)
    if len(q) == 1:
        return q[0]
    else:
        return q


def saturation_mixing_ratio(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Calculate saturation mixing ratio.

    Arguments
    ---------
    temperature: iris.cube.Cube | iris.cube.CubeList
        Cubes of temperature in Kelvin.
    pressure: iris.cube.Cube | iris.cube.CubeList
        Cubes of pressure.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Saturation mixing ratio in kg/kg.

    Notes
    -----
    The saturation mixing ratio is required to help calculate the relative
    humidity and other diagnostics with respect to the mixing ratio. It can
    be calculated from

    .. math:: w = \epsilon \frac{e}{P - e}

    for w the mixing ratio, :math:`\epsilon` the ratio between the mixing ratio
    of dry and moist air equating to 0.62197, P the pressure and e the vapour
    pressure. To ensure that the saturation mixing ratio (:math:`w_s`) is
    calculated the vapour pressure calculated should be with the (dry-bulb)
    temperature to ensure it is the saturated vapour pressure.

    All cubes need to be on the same grid.

    Examples
    --------
    >>> w_s = humidity.saturation_mixing_ratio(temperature, pressure)
    """
    w = iris.cube.CubeList([])
    for T, P in zip(iter_maybe(temperature), iter_maybe(pressure), strict=True):
        P = convert_units(P, "hPa")
        mr = (EPSILON * vapour_pressure(T)) / (P - vapour_pressure(T))
        mr.units = "kg/kg"
        mr.rename("saturation_mixing_ratio")
        w.append(mr)
    if len(w) == 1:
        return w[0]
    else:
        return w


def saturation_specific_humidity(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Calculate saturation specific humidity.

    Arguments
    ---------
    temperature: iris.cube.Cube | iris.cube.CubeList
        Cubes of temperature in Kelvin.
    pressure: iris.cube.Cube | iris.cube.CubeList
        Cubes of pressure.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Saturation specific humidity in kg/kg.

    Notes
    -----
    The saturation specific humidity is required to help calculate the relative
    humidity and other diagnostics with respect to the mixing ratio. It can
    be calculated from

    .. math:: q = \epsilon \frac{e}{P}

    for q the specific humidity, :math:`\epsilon` the ratio between the mixing ratio
    of dry and moist air equating to 0.62197, P the pressure and e the vapour
    pressure. To ensure that the saturation specific humidity (:math:`q_{sat}`) is
    calculated the vapour pressure calculated should be with the (dry-bulb)
    temperature to ensure it is the saturated vapour pressure.

    All cubes need to be on the same grid.

    Examples
    --------
    >>> q_sat = humidity.saturation_specific_humidity(temperature, pressure)
    """
    q = iris.cube.CubeList([])
    for T, P in zip(iter_maybe(temperature), iter_maybe(pressure), strict=True):
        P = convert_units(P, "hPa")
        sh = (EPSILON * vapour_pressure(T)) / P
        sh.units = "kg/kg"
        sh.rename("saturation_specific_humidity")
        q.append(sh)
    if len(q) == 1:
        return q[0]
    else:
        return q


def mixing_ratio_from_relative_humidity(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
    relative_humidity: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Calculate the mixing ratio from RH.

    Arguments
    ---------
    temperature: iris.cube.Cube | iris.cube.CubeList
        Cubes of temperature in Kelvin.
    pressure: iris.cube.Cube | iris.cube.CubeList
        Cubes of pressure.
    relative_humidity: iris.cube.Cube | iris.cube.CubeList
        Cubes of relative humidity.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Calculated mixing ratio from relative humidity in kg/kg.

    Notes
    -----
    The mixing ratio can be calculated from temperature, pressure, and
    relative humidity using the following relation

    .. math:: w = RH * w_s

    for w the mixing ratio, :math:`w_s` the saturation mixing ratio, and
    RH the relative humidity. RH is converted to dimensionless fraction rather
    than percentage.

    The operator uses `humidity.saturation_mixing_ratio` to calculate the
    saturation mixing ratio from the temperature and pressure. The relative
    humidity is converted into a decimal before the multiplication occurs.

    All cubes need to be on the same grid.

    Examples
    --------
    >>> w = humidity.mixing_ratio_from_relative_humidity(T, P, RH)
    """
    w = iris.cube.CubeList([])
    for T, P, RH in zip(
        iter_maybe(temperature),
        iter_maybe(pressure),
        iter_maybe(relative_humidity),
        strict=True,
    ):
        RH = convert_units(RH, "1")
        mr = saturation_mixing_ratio(T, P) * RH
        mr.rename("mixing_ratio")
        mr.units = "kg/kg"
        w.append(mr)
    if len(w) == 1:
        return w[0]
    else:
        return w


def specific_humidity_from_relative_humidity(
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
    relative_humidity: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Calculate the specific humidity from relative humidity.

    Arguments
    ---------
    temperature: iris.cube.Cube | iris.cube.CubeList
        Cubes of temperature in Kelvin.
    pressure: iris.cube.Cube | iris.cube.CubeList
        Cubes of pressure.
    relative_humidity: iris.cube.Cube | iris.cube.CubeList
        Cubes of relative humidity.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Calculated specific humidity from relative humidity in kg/kg.

    Notes
    -----
    The specific humidity can be calculated from temperature, pressure, and
    relative humidity using the following relation

    .. math:: q = RH * q_{sat}

    for q the specific humidity, :math:`q_{sat}` the saturation specific
    humidity, and RH the relative humidity.

    The operator uses `humidity.saturation_specific_humidity` to calculate the
    saturation specific humidity from the temperature and pressure. The relative
    humidity is converted into a decimal before the multiplication occurs.

    All cubes need to be on the same grid.

    Examples
    --------
    >>> q = humidity.specific_humidity_from_relative_humidity(T, P, RH)
    """
    q = iris.cube.CubeList([])
    for T, P, RH in zip(
        iter_maybe(temperature),
        iter_maybe(pressure),
        iter_maybe(relative_humidity),
        strict=True,
    ):
        RH = convert_units(RH, "1")
        sh = saturation_specific_humidity(T, P) * RH
        sh.rename("specific_humidity")
        sh.units = "kg/kg"
        q.append(sh)
    if len(q) == 1:
        return q[0]
    else:
        return q


def relative_humidity_from_mixing_ratio(
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList,
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Convert mixing ratio to relative humidity.

    Arguments
    ---------
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList
        Cubes of mixing ratio.
    temperature: iris.cube.Cube | iris.cube.CuebList
        Cubes of temperature in Kelvin.
    pressure: iris.cube.Cube | iris.cube.CubeList
        Cubes of pressure.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Relative humidity calculated from mixing ratio.

    Notes
    -----
    The relative humidity can be calculated from the mixing ratio following

    .. math:: RH = \frac{w}{w_s}

    for RH the relative humidity, w the mixing ratio, and :math:`w_s` the
    saturation mixing ratio. The saturation mixing ratio is calculated using
    `humidity.saturation_mixing_ratio`.

    The RH varies predominatly between zero (completely dry) and one (saturated).
    Values larger than one are possible and imply supersaturation.

    All cubes must be on the same grid.

    Examples
    --------
    >>> RH = humidity.relative_humidity_from_mixing_ratio(w, T, P)
    """
    RH = iris.cube.CubeList([])
    for W, T, P in zip(
        iter_maybe(mixing_ratio),
        iter_maybe(temperature),
        iter_maybe(pressure),
        strict=True,
    ):
        rel_h = W / saturation_mixing_ratio(T, P)
        rel_h.rename("relative_humidity")
        rel_h = convert_units(rel_h, "%")
        RH.append(rel_h)
    if len(RH) == 1:
        return RH[0]
    else:
        return RH


def relative_humidity_from_specific_humidity(
    specific_humidity: iris.cube.Cube | iris.cube.CubeList,
    temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Convert specific humidity to relative humidity.

    Arguments
    ---------
    specific_humidity: iris.cube.Cube | iris.cube.CubeList
        Cubes of specific humidity.
    temperature: iris.cube.Cube | iris.cube.CuebList
        Cubes of temperature in Kelvin.
    pressure: iris.cube.Cube | iris.cube.CubeList
        Cubes of pressure.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Relative humidity calculated from specific humidity.

    Notes
    -----
    The relative humidity can be calculated from the specific humidity following

    .. math:: RH = \frac{q}{q_{sat}}

    for RH the relative humidity, q the specific humidity, and :math:`q_{sat}` the
    saturation specific humidity. The saturation specific humidity is calculated using
    `humidity.saturation_specific_humidity`.

    The RH varies predominantly between zero (completely dry) and one (saturated).
    Values larger than one are possible and imply supersaturation.

    All cubes must be on the same grid.

    Examples
    --------
    >>> RH = humidity.relative_humidity_from_specific_humidity(q, T, P)
    """
    RH = iris.cube.CubeList([])
    for Q, T, P in zip(
        iter_maybe(specific_humidity),
        iter_maybe(temperature),
        iter_maybe(pressure),
        strict=True,
    ):
        rel_h = Q / saturation_specific_humidity(T, P)
        rel_h.rename("relative_humidity")
        rel_h = convert_units(rel_h, "%")
        RH.append(rel_h)
    if len(RH) == 1:
        return RH[0]
    else:
        return RH


def precipitable_water(
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Calculate the precipitable water.

    Arguments
    ---------
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList
        A cube or cubelist of the mixing ratio. It can be
        calculated within a recipe or a direct model output.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        A cube or cubelist of the precipitable water.

    Notes
    -----
    The precipitable water is the total depth of liquid water produced by
    condensing all of the moisture in a column of the atmopshere.

    It can be calculated following [Stull2000]_ as

    .. math:: pw = frac{1}{\rho_w} \int w dz

    for pw the precipitable water, ..math::\rho_{w} the density of water,
    w the mixing ratio, and z the height. It is integrated from the surface
    to the top of the atmosphere.

    Generally, the precipitable water is widely applicable across the globe.
    It is likely that larger precipitation totals are associated with greater
    precipitable water. However, this is not strictly the case and you can get
    lower precipitable water values with large precipitaiton amounts
    (e.g. [Daviesetal24]_). Therefore, caution is needed with its interpretation.
    A diagnostic such as saturation fraction maybe more beneficial (e.g. [Daviesetal26]_).

    Currently, it is assumed that a cube is given with dimensions of the order
    [realization, time, height, latitude, longitude] for a five dimension cube,
    and derivatives thereof for 4 and 3 Dimension cubes (i.e., remove realization,
    and time as appropriate).

    Examples
    --------
    >>> pwat = humidity.precipitable_water(mixing_ratio)

    References
    ----------
    .. [Daviesetal24] Davies, P.A., Fowler, H.J, Villalobos-Herrera, R.,
       Slingo, J., Flack, D.L.A., and Taszarek, M (2024)
       "A New Conceptual Model for Understanding and Predicting Life-Threatening
       Rainfall Extremes." Weather and Climate Extremes, vol. 45, 100696,
       doi: 10.1016/j.wace.2024.100696
    .. [Daviesetal26] Davies, P. A., Flack, D. L. A., Pirret, J., Fowler, H. J.
       (2026) "Application of the Davies Four-Stage Conceptual Model for
       Life-Threatening Rainfall Extremes on the April 2024 United Arab Emirates
       and Oman Floods." Weather and Climate Extremes, vol. 51, 100846.
       doi:10.1016/j.wace.2025.100846
    .. [Stull2000] Stull, R.B., (2000) "Meteorology for Scientists and Engineers",
       2nd Edition, Brooks/Cole, California, USA, 502 pp.
    """
    precipitable_water = iris.cube.CubeList([])
    for w in iter_maybe(mixing_ratio):
        # Integrate the data in the vertical using np.trapezoid
        # (following trapezoid rule).
        pw = np.trapezoid(
            w.data,
            x=w.coord("level_height").points[:],
            axis=get_cube_coordindex(w, "level_height"),
        )
        # Determine array information of input cube to get
        # correct cube to copy across to.
        if len(w.coord("realization").points) != 1 and len(w.coord("time").points) != 1:
            pwat = w[:, :, 0, :, :].copy()
        elif (
            len(w.coord("realization").points) != 1 and len(w.coord("time").points) == 1
        ):
            pwat = w[:, 0, :, :].copy()
        elif (
            len(w.coord("time").points) != 1 and len(w.coord("realization").points) == 1
        ):
            pwat = w[:, 0, :, :].copy()
        else:
            pwat = w[0, :, :].copy()
        # Create the data array, rename, and correct units.
        pwat.data = pw
        pwat.rename("precipitable_water")
        # Setting units to mm to account for normalization by density of water.
        pwat.units = "mm"
        precipitable_water.append(pwat)
    # Output the data.
    if len(precipitable_water) == 1:
        return precipitable_water[0]
    else:
        return precipitable_water


def saturation_precipitable_water(
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList,
    relative_humidity: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Calculate saturation precipitable water.

    Arguments
    ---------
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList
        A cube or cubelist of the mixing ratio. It can be
        calculated within a recipe or a direct model output.
    relative_humidity: iris.cube.Cube | iris.cube.CubeList
        A cube or cubelist of the relative humidity. It can
        either be calculated or used as model output.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        A cube or cubelist of the saturation precipitable water.

    Notes
    -----
    The saturation precipitable water is equivalent to the precipitable
    water assuming that the atmosphere was fully saturated.

    It can be calculated following [Raymondetal2009]_ as

    .. math:: spw = frac{1}{\rho_w} \int \frac{w}{RH} dz

    for spw the saturated precipitable water, ..math::\rho_{w} the density of water,
    w the mixing ratio, RH the relative humidity (as a decimal) and z the height.
    It is integrated from the surface to the top of the atmosphere.

    It is applicable throughout the globe and is, perhaps, best considered
    in relation to the precipitable water. A useful way to do this is
    via the saturation fraction.

    Currently, it is assumed that a cube is given with dimensions of the order
    [realization, time, height, latitude, longitude] for a five dimension cube,
    and derivatives thereof for 4 and 3 Dimension cubes (i.e., remove realization,
    and time as appropriate).

    Examples
    --------
    >>> sat_pwat = humidity.saturated_precipitable_water(mixing_ratio, RH)

    References
    ----------
    .. [Raymondetal2009] Raymond, D.J., Sessions, S.L., Sobel, A.H.,  Fuchs, Z.
       (2009) "The Mechanics of Gross Moist Stability" Journal of Advances in
       Modelling Earth Systems, vol. 1, 20 pp. doi: 10.3894/JAMES.2009.1.9
    """
    saturation_precipitable_water = iris.cube.CubeList([])
    for w, rh in zip(
        iter_maybe(mixing_ratio), iter_maybe(relative_humidity), strict=True
    ):
        # Integrate the data in the vertical using np.trapezoid
        # (following trapezoid rule).
        rh = convert_units(rh, "1")
        spw = np.trapezoid(
            (w / rh).data,
            x=w.coord("level_height").points[:],
            axis=get_cube_coordindex(w, "level_height"),
        )
        # Determine array information of input cube to get
        # correct cube to copy across to.
        if len(w.coord("realization").points) != 1 and len(w.coord("time").points) != 1:
            satpw = w[:, :, 0, :, :].copy()
        elif (
            len(w.coord("realization").points) != 1 and len(w.coord("time").points) == 1
        ):
            satpw = w[:, 0, :, :].copy()
        elif (
            len(w.coord("time").points) != 1 and len(w.coord("realization").points) == 1
        ):
            satpw = w[:, 0, :, :].copy()
        else:
            satpw = w[0, :, :].copy()
        # Store the data for output, rename cube, and correct units.
        satpw.data = spw
        satpw.rename("saturation_precipitable_water")
        # Setting units to mm to account for normalization by density of water.
        satpw.units = "mm"
        saturation_precipitable_water.append(satpw)
    # Output cube/cubelist.
    if len(saturation_precipitable_water) == 1:
        return saturation_precipitable_water[0]
    else:
        return saturation_precipitable_water


def saturation_fraction(
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList,
    relative_humidity: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    r"""Calculate saturation fraction.

    Arguments
    ---------
    mixing_ratio: iris.cube.Cube | iris.cube.CubeList
        A cube or cubelist of the mixing ratio. It can be
        calculated within a recipe or a direct model output.
    relative_humidity: iris.cube.Cube | iris.cube.CubeList
        A cube or cubelist of the relative humidity. It can be
        calculated within a recipe or used as a direct model output.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        A cube or cubelist of the saturation fraction.

    Notes
    -----
    The saturation fraction indicates how moist a column of the atmosphere
    is. A value close to one implies that the atmosphere is fully saturated
    throughout the entire column. Smaller values imply the atmosphere is
    drier throughout the column. It is based around ideas of specific entropy
    ([Zengetal05]_) but can be simplified to an approximation following [Daviesetal2026]_.

    It can be approximated following [Raymondetal09]_ as

    .. math:: saturation_fraction = \frac{precipitable_water}{saturation_precipitable_water}

    and can be used throughout the globe with the same interpretation.

    For a recent example, [Daviesetal2026]_ have applied the concept to their
    conceptual model for extreme rainfall. Thus it is a potentially useful diagnostic
    to consider for extreme events, and is thought of as more reliable than
    using precipitable water on its own.

    Currently, it is assumed that a cube is given with dimensions of the order
    [realization, time, height, latitude, longitude] for a five dimension cube,
    and derivatives thereof for 4 and 3 Dimension cubes (i.e., remove realization,
    and time as appropriate).

    Examples
    --------
    >>> sf = humidity.saturation_fraction(mixing_ratio, relative_humidity)

    References
    ----------
    .. [Daviesetal2026] Davies, P. A., Flack, D. L. A., Pirret, J., Fowler, H. J.
       (2026) "Application of the Davies Four-Stage Conceptual Model for
       Life-Threatening Rainfall Extremes on the April 2024 United Arab Emirates
       and Oman Floods." Weather and Climate Extremes, vol. 51, 100846.
       doi:10.1016/j.wace.2025.100846
    .. [Raymondetal09] Raymond, D.J., Sessions, S.L., Sobel, A.H.,  Fuchs, Z.
       (2009) "The Mechanics of Gross Moist Stability" Journal of Advances in
       Modelling Earth Systems, vol. 1, 20 pp. doi: 10.3894/JAMES.2009.1.9
    .. [Zengetal05] Zeng, X., Tao, W-K, and Simpson, J. (2005) "An Equation for Moist
       Entropy in a Precipitating and Icy Atmosphere" Journal of the Atmospheric Sciences,
       vol. 2, 4293-4309, doi: 10.1175/JAS3570.1
    """
    saturation_fraction = iris.cube.CubeList([])
    for w, rh in zip(
        iter_maybe(mixing_ratio), iter_maybe(relative_humidity), strict=True
    ):
        # Calculate both precipitable water and saturation
        # precipitable water.
        pw = precipitable_water(w)
        spw = saturation_precipitable_water(w, rh)
        # Calculate the saturation fraction by taking the ratio.
        sf = pw / spw
        # Rename the cube and append to cubelist.
        sf.rename("saturation_fraction")
        saturation_fraction.append(sf)
    # Output the cube/cubelist.
    if len(saturation_fraction) == 1:
        return saturation_fraction[0]
    else:
        return saturation_fraction
