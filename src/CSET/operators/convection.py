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

"""A module containing different diagnostics for convection.

The diagnostics are calculated from output from the Unified Model, although
precalculated values in the required input form may also be used.

"""

import copy
import logging
import warnings

import numpy as np


def cape_ratio(SBCAPE, MUCAPE, MUCIN, MUCIN_thresh=-75.0):
    r"""Ratio of two fields, one filtered to allow physical values to be output.

    Parameters
    ----------
    SBCAPE: Cube
        Surface-based convective available potential energy as calculated by the
        model. If using the UM please use STASH ``m01s20i114``
    MUCAPE: Cube
        Most-unstable convective available potential energy as calculated by the
        model. If using the UM please use STASH ``m01s20i112``
    MUCIN: Cube
        Most-unstable convective inhibition associated with the most-unstable
        ascent as calculated by the model. If using the UM please use STASH
        ``m01s20i113``
    MUCIN_thresh: float, optional, default is -75. J/kg.
        Threshold to filter the MUCAPE by values are realistically realisable.

    Returns
    -------
    Cube

    Notes
    -----
    This diagnostic is based on Clark et al. (2012) [Clarketal2012]_. It is
    based around the idea that for elevated convection the convective
    instability is not based at the surface. This utilises two flavours of CAPE:
    the surface-based CAPE (SBCAPE) and the most-unstable CAPE (MUCAPE). The
    MUCAPE is filtered by the MUCIN associated with that parcel's ascent to
    ensure that any CAPE can at least theoretically be released. The default
    value is set at -75 J/kg but it can be changes depending on location and
    users requirements.

    .. math:: 1 - (\frac{SBCAPE}{MUCAPE})

    The ratio is defined in this way such that if SBCAPE=MUCAPE the ratio will
    equal 1. If the ratio was reversed when MUCAPE exists and SBCAPE is zero the
    ratio would be undefined.

    The diagnostic varies smoothly between zero and unity. A value of 0 implies
    an environment is suitable for surface-based convection. A value of 1
    implies an environment is suitable for elevated convection. Values between
    imply transition convection with values closer to one imply elevated
    convection is more likely and values closer to zero implying that
    surface-based convection is more likely.

    Further details about this diagnostic for elevated convection identification
    can be found in Flack et al. (2023) [FlackCAPE2023]_.

    Expected applicability ranges: Convective-scale models will be noisier than
    parametrized models as they are more responsive to the convection, and thus
    it may be more sensible to view as a larger spatial average rather than on
    the native resolution.

    Interpretation notes: UM stash for CAPE and CIN are calculated at the end of
    the timestep. Therefore this diagnostic is applicable after precipitation
    has occurred, not before as is the usual interpretation of CAPE related
    diagnostics.

    References
    ----------
    .. [Clarketal2012] Clark, A. J., Kain J. S., Marsh P. T., Correia J., Xue
       M., and Kong F., (2012) "Forecasting tornado pathlengths using a
       three-dimensional object identification algorithm applied to
       convection-allowing forecasts." Weather and Forecasting, vol. 27,
       1090–1113, doi: 10.1175/WAF-D-11-00147.1
    .. [FlackCAPE2023] Flack, D.L.A., Lehnert, M., Lean, H.W., and Willington,
       S. (2023) "Characteristics of Diagnostics for Identifying Elevated
       Convection over the British Isles in a Convection-Allowing Model."
       Weather and Forecasting, vol. 30, 1079-1094, doi: 10.1175/WAF-D-22-0219.1

    Examples
    --------
    >>> CAPE_ratios=convection.cape_ratio(
            SBCAPE,MUCAPE,MUCIN)
    >>> iplt.pcolormesh(CAPE_ratios[0,:,:],cmap=mpl.cm.RdBu)
    >>> plt.gca().coastlines('10m')
    >>> plt.colorbar()
    >>> plt.clim(0,1)
    >>> plt.show()

    >>> CAPE_ratios=convection.cape_ratio(
            SBCAPE,MUCAPE,MUCIN,MUCIN_thresh=-1.5)
    >>> iplt.pcolormesh(CAPE_ratios[0,:,:],cmap=mpl.cm.RdBu)
    >>> plt.gca().coastlines('10m')
    >>> plt.clim(0,1)
    >>> plt.colorbar()
    >>> plt.show()
    """
    # Load in the data into the new arrays.
    MUCAPE_data = copy.deepcopy(MUCAPE.data)
    if isinstance(MUCAPE_data, np.ma.MaskedArray):
        MUCAPE_data = MUCAPE_data.filled(np.nan)
    # Remove all MUCAPE below MUCIN threshold.
    MUCAPE_data[MUCIN.data <= MUCIN_thresh] = np.nan
    with warnings.catch_warnings():
        # Ignore possible divide by zero warnings, as they are replaced by NaNs.
        warnings.filterwarnings("ignore", category=RuntimeWarning)
        # Now calculate the main diagnostic.
        EC_Flagb = 1 - (SBCAPE.data / MUCAPE_data)
        if isinstance(EC_Flagb, np.ma.MaskedArray):
            EC_Flagb = EC_Flagb.filled(np.nan)
    # Filter to reduce NaN values and -inf values for plotting ease.
    # There are multiple types of NaN values so need to convert them all to same type.
    EC_Flagb[np.isnan(EC_Flagb)] = np.nan
    EC_Flagb[np.isinf(EC_Flagb)] = np.nan
    # Take the coordinates from an existing cube and replace the data.
    cape_ratio_cube = SBCAPE.copy()
    cape_ratio_cube.data = EC_Flagb
    # Rename and remove STASH code.
    cape_ratio_cube.var_name = "cape_ratio"
    cape_ratio_cube.attributes.pop("STASH", None)
    return cape_ratio_cube


def inflow_layer_properties(EIB, BLheight, Orography):
    r"""Filter to create a binary mask identifying elevated convection.

    Parameters
    ----------
    EIB: Cube
        Effective inflow layer base (precalculated or as identified by the
        model). If using the UM please use STASH ``m01s20i119``.
    BLheight: Cube
        Boundary layer height (precalculated or as identified by the model). If
        using the UM please use STASH ``m01s00i025``.
    Orography: Cube
        Model or actual orography, expected to be 2 dimensional. If 3 or 4
        dimensional cube given converts to 2 dimensions assuming static
        orography field in ensemble realization and time. If using the UM please
        use STASH ``m01s00i033``.

    Returns
    -------
    Cube

    Notes
    -----
    This diagnostic is based on the concept of an effective inflow layer. This
    concept was first introduced by Thompson et al. (2007) [Thompsonetal2007]_.
    The inflow layer defined the region of air that is most likely to be
    ingested into the convective event. It is defined by thresholding the CAPE
    and CIN values: CAPE > 100 J/kg and \|CIN\| < 250 J/kg.

    To turn this into a diagnostic for elevated convection the inflow layer base
    is filtered against the boundary layer height. The model orography is added
    to the boundary layer height to ensure reference height consistency as the
    BL height is defined above ground level and the inflow layer base is defined
    above sea level in the model output.

    .. math:: EIB > BLheight + Orography

    This is a binary diagnostic. It has a value of 0 to imply the environment is
    suitable for surface-based convection. It has a value of 1 to indicate the
    environment is suitable to produce elevated convection.

    Further details about this diagnostic for elevated convection identification
    can be found in Flack et al. (2023) [Flackinf2023]_.

    Expected applicability ranges: Convective-scale models will be noisier than
    parametrized models as they are more responsive to the convection, and thus
    it may be more sensible to view as a larger spatial average rather than at
    native resolution.

    Interpretation notes: The effective inflow layer base diagnostic from UM
    STASH is dependent upon the UM CAPE and CIN diagnostics. These diagnostics
    are calculated at the end of the timestep. Therefore this diagnostic is
    applicable after precipitation has occurred, not before as is the usual
    interpretation of CAPE related diagnostics.

    You might encounter warnings with the following text ``Orography assumed not
    to vary with ensemble member.`` or ``Orography assumed not to vary with time
    and ensemble member.`` these warnings are expected when the orography files
    are not 2-dimensional, and do not cause any problems unless ordering is not
    as expected.

    References
    ----------
    .. [Thompsonetal2007] Thompson, R. L. Mead, C. M., and Edwards, R., (2007)
       "Effective Storm-Relative Helicity and Bulk Shear in Supercell
       Thunderstorm Environments." Weather and Forecasting, vol. 22, 102-115,
       doi: 10.1175/WAF969.1
    .. [Flackinf2023] Flack, D.L.A., Lehnert, M., Lean, H.W., and Willington, S.
       (2023) "Characteristics of Diagnostics for Identifying Elevated
       Convection over the British Isles in a Convection-Allowing Model."
       Weather and Forecasting, vol. 30, 1079-1094, doi: 10.1175/WAF-D-22-0219.1

    Examples
    --------
    >>> Inflow_properties=convection.inflow_layer_properties(EIB,BLheight,Orography)
    >>> iplt.pcolormesh(Inflow_properties[0,:,:],cmap=mpl.cm.Purples)
    >>> plt.gca().coastlines('10m')
    >>> plt.colorbar()
    >>> plt.clim(0,1)
    >>> plt.show()

    """
    # Setup new array for output of the diagnostic.
    EC_Flagd = np.zeros(EIB.shape)
    # Check dimensions for Orography cube and replace with 2D array if not 2D.
    if Orography.ndim == 3:
        Orography = Orography.slices_over("realization").next()
        logging.warning("Orography assumed not to vary with ensemble member")
    elif Orography.ndim == 4:
        Orography = Orography.slices_over(("time", "realization")).next()
        logging.warning("Orography assumed not to vary with time or ensemble member. ")
    # Masked arrays are not respected, so convert masked values into NaNs.
    if isinstance(EIB.data, np.ma.MaskedArray):
        EIB.data = EIB.data.filled(np.nan)
    # Change points where Effective inflow layer base is larger than boundary
    # layer height to 1 implying elevated convection.
    EC_Flagd[EIB.data > (BLheight.data + Orography.data)] = 1.0
    # Take the coordinates from an existing cube and replace the data.
    inflow_properties_cube = EIB.copy()
    inflow_properties_cube.data = EC_Flagd
    # Rename and remove STASH code.
    inflow_properties_cube.var_name = "inflow_layer_properties"
    inflow_properties_cube.attributes.pop("STASH", None)
    return inflow_properties_cube
