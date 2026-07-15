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

"""Operators to calculate kinematic heat fluxes from covariances."""

import iris
import iris.cube
from cf_units import Unit
from iris.cube import Cube, CubeList

from CSET._common import iter_maybe
from CSET.operators._atmospheric_constants import CPD, LV, RD


def sensible_heat_flux_from_covariance(
    wt_flux: iris.cube.Cube | iris.cube.CubeList,
    air_temperature: iris.cube.Cube | iris.cube.CubeList,
    pressure: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.CubeList:
    """
    Convert turbulent temperature covariance into sensible heat flux.

    Computes:
        SHF = rho * CPD * w'T'

    where:
        rho = pressure / (RD * temperature)

    Parameters
    ----------
    wt_flux : iris.cube.Cube or iris.cube.CubeList
        Turbulent temperature covariance (w'T').

    air_temperature : iris.cube.Cube or iris.cube.CubeList
        Air temperature.

    pressure : iris.cube.Cube or iris.cube.CubeList
        Air pressure.

    Returns
    -------
    iris.cube.CubeList
        Surface upward sensible heat flux cube(s).
    """
    from cf_units import Unit

    out = iris.cube.CubeList()
    for wt_cube, temp_cube, pres_cube in zip(
        iter_maybe(wt_flux),
        iter_maybe(air_temperature),
        iter_maybe(pressure),
        strict=True,
    ):
        # Unit conversions
        temp_K = temp_cube.copy()
        temp_K.convert_units("K")
        pres_Pa = pres_cube.copy()
        pres_Pa.convert_units("Pa")
        wt_cov = wt_cube.copy()

        # Treat degC covariance numerically as K covariance
        if str(wt_cov.units) == "degC m s-1":
            wt_cov.units = Unit("K m s-1")

        # Density and SHF
        rho_air = pres_Pa / (RD * temp_K)
        shf = CPD * rho_air * wt_cov

        shf.units = Unit("W m-2")
        shf.rename("surface_upward_sensible_heat_flux")
        # Keep compatibility with existing tests/output
        shf.var_name = "surface_upward_sensible_heat_flux"

        out.append(shf)

    return out[0] if len(out) == 1 else out


def latent_heat_units(
    cubes: Cube | CubeList,
    **kwargs,
) -> Cube | CubeList:
    """
    Convert covariance into latent heat flux units.

    This operator converts any cube with units convertible to kg m-2 s-1
    (i.e. water mass flux) into latent heat flux (W m-2) by multiplying
    by a constant latent heat of vaporisation.

    No attempt is made to distinguish between turbulent fluxes (e.g. w'q')
    and other water mass fluxes. This generalisation seems reasonable
    given that interpreting rainfall or dewfall, for example, as an
    equivalent heat flux is physically meaningful.

    This function operates on one or more Iris cubes. Any cube with
    units convertible to mass flux (kg m-2 s-1) is multiplied by a
    constant latent heat of vaporisation to produce a latent heat flux.
    Cubes with incompatible, missing, or unknown units are passed through
    unchanged.

    Parameters
    ----------
    cubes : Cube or CubeList
        Input cube(s), typically containing w'q' covariance or other flux-like
        quantities.

    **kwargs : dict
        Unused; accepted for interface consistency with other operators.

    Returns
    -------
    Cube or CubeList
        Output cube(s) where:
        - Cubes with units convertible to kg m-2 s-1 are converted to W m-2.
        - All other cubes are returned unchanged.
        - The return type matches the input type (single Cube or CubeList).

    Notes
    -----
    - The conversion uses a fixed latent heat of vaporisation:
          LV = 2.5 × 10^6 J kg-1
    - In reality, Lc varies with temperature (~5% variation between -20 °C
      and +40 °C). This dependency is currently neglected but could be
      included in future improvements.
    - This function does not attempt to identify specific variables; it relies
      solely on unit convertibility to determine applicability.
    """
    REQUIRED_UNITS = Unit("kg m-2 s-1")
    OUTPUT_UNITS = Unit("W m-2")

    out = iris.cube.CubeList()
    for cube in iter_maybe(cubes):
        # ACT ON MASS FLUXES
        if cube.units is None or cube.units.is_unknown():
            out.append(cube)
            continue
        if not cube.units.is_convertible(REQUIRED_UNITS):
            # e.g. if UM LE or some other diagnostic — leave untouched
            out.append(cube)
            continue

        cube_a = cube.copy()
        cube_a = cube_a * LV
        cube_a.units = cube.units * Unit("J kg-1")
        cube_a.convert_units(OUTPUT_UNITS)
        out.append(cube_a)

    return out[0] if len(out) == 1 else out
