#!/usr/bin/env python3
"""A module containing different diagnostics to identify elevated convection.

The diagnostics are calculated from output from the Unified Model, although
precalculated values in the required input form may also be used.

Three diagnostics are defined in this module:
- cape_ratio - this takes the ratio between the SBCAPE and the MUCAPE,
- inflow_layer_properties - this compares the inflow layer base with the
                            boundary layer height,
- combined diagnostic - this multiples the two previous diagnostics together.

Version History
---------------
Version 1: 27 October 2022
    Code added with comments for all diagnostics.
Version 2: 14 November 2022
    Full documentation added for all diagnostics.
Version 3: 14 November 2023
    Style and documentation improvements from code review.
"""
################################################################################
#####                        LOAD PYTHON LIBRARIES                         #####
################################################################################

import copy

import numpy as np

################################################################################
#####                  DIAGNOSTIC 1: 1 - (SBCAPE/MUCAPE)                   #####
################################################################################


def cape_ratio(SBCAPE, MUCAPE, MUCIN, MUCIN_thresh=-75.0):
    r"""Ratio of two fields, one filtered to allow physical values to be output.

    Parameters
    ----------
    SBCAPE: cube
        Surface-based convective available potential energy as calculated by the
        model.
        Stash: m01s20i114
    MUCAPE: cube
        Most-unstable convective available potential energy as calculated by the
        model.
        Stash: m01s20i112
    MUCIN: cube
        Most-unstable convective inhibition associated with the most-unstable
        ascent as calculated by the model.
        Stash: m01s20i113
    MUCIN_thresh: float, optional, default is -75. J/kg.
        Threshold to filter the MUCAPE by values are are realistically
        realisable.

    Returns
    -------
    ndarray

    Notes
    -----
    This diagnostic is based on Clark et al. [1]_. It is based around the idea
    that for elevated convection the convective instability is not based at the
    surface. This utilises two flavours of CAPE: the surface-based CAPE (SBCAPE)
    and the most-unstable CAPE (MUCAPE). The MUCAPE is filtered by the MUCIN
    associated with that parcel's ascent to ensure that any CAPE can at least
    theoretically be released. The default value is set at -75 J/kg but it can
    be changes depending on location and users requirements.

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
    can be found in [2]_.

    References
    ----------
    .. [1] Clark, A. J., Kain J. S., Marsh P. T., Correia J., Xue M., and Kong
       F., (2012) "Forecasting tornado pathlengths using a three-dimensional
       object identification algorithm applied to convection-allowing
       forecasts." Weather and Forecasting, vol. 27, 1090–1113, doi:
       10.1175/WAF-D-11-00147.1
    .. [2] Flack, D.L.A., Lehnert, M., Lean, H.W., and Willington, S. (2023)
       "Characteristics of Diagnostics for Identifying Elevated
       Convection over the British Isles in a Convection-Allowing Model."
       Weather and Forecasting. 38: 1079-1094. doi: 10.1175/WAF-D-22-0219.1

    Examples
    --------
    >>> CAPE_ratios=ecd.cape_ratio(SBCAPE,MUCAPE,MUCIN)
    >>> #convert to cube before this next step
    >>> iplt.pcolormesh(CAPE_ratios[0,:,:],cmap=mpl.cm.Purples)
    >>> plt.gca().coastlines('10m')
    >>> plt.colorbar()
    >>> plt.clim(0,1)
    >>> plt.show()

    >>> CAPE_ratios_filter=ecd.cape_ratio(SBCAPE,MUCAPE,MUCIN,
                                          MUCIN_thresh=-1.5)
    >>> #convert to cube before this next step
    >>> iplt.pcolormesh(CAPE_ratios_filter[0,:,:],cmap=mpl.cm.Purples)
    >>> plt.gca().coastlines('10m')
    >>> plt.clim(0,1)
    >>> plt.colorbar()
    >>> plt.show()
    """
    # Setup new arrays so do not overwrite cubes.
    SBCAPE_data = np.zeros(np.shape(SBCAPE.data))
    MUCAPE_data = np.zeros(np.shape(MUCAPE.data))
    # Load in the data into the new arrays.
    SBCAPE_data = copy.deepcopy(SBCAPE.data)
    MUCAPE_data = copy.deepcopy(MUCAPE.data)
    # Filter MUCAPE by MUCIN to all for possible (realistic) MUCAPE.
    MUCAPE_data[MUCIN.data <= MUCIN_thresh] = 0.0
    # Now calculate the main diagnostic
    EC_Flagb = 1 - (SBCAPE_data / MUCAPE_data)
    # Filter to reduce NaN values and -inf values for plotting ease.
    EC_Flagb[np.isnan(EC_Flagb)] = np.nan
    EC_Flagb[np.abs(EC_Flagb) == np.inf] = np.nan
    # Take the coordinates from an existing cube and replace the data.
    cape_ratio_cube = SBCAPE.copy()
    cape_ratio_cube.data = EC_Flagb
    # Rename and remove STASH code.
    cape_ratio_cube.var_name = "cape_ratio"
    cape_ratio_cube.attributes.pop("STASH", None)
    print(cape_ratio_cube)
    return cape_ratio_cube
