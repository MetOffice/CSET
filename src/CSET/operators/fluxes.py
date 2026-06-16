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


def _exactly_one(matches, role):
    if len(matches) == 0:
        raise ValueError(f"sensible_heat_units could not identify a unique {role} cube")
    if len(matches) > 1:
        names = [getattr(c, "var_name", None) or c.name() for c in matches]
        raise ValueError(
            f"sensible_heat_units found multiple possible {role} cubes: {names}"
        )
    return matches[0]


def _is_p_cube(cube):
    return (
        cube.units is not None
        and not cube.units.is_unknown()
        and cube.units.is_convertible(Unit("Pa"))
    )


def _is_T_cube(cube):
    if cube.units is None or cube.units.is_unknown():
        return False
    return cube.units.is_convertible(Unit("K")) or cube.units.is_convertible(
        Unit("degC")
    )


def _is_wt_covar_cube(cube):
    if cube.units is None or cube.units.is_unknown():
        return False
    # turbulence covariance may be recorded either as K m s-1
    # or degC m s-1; these are equivalent
    return cube.units.is_convertible(Unit("K m s-1")) or cube.units.is_convertible(
        Unit("degC m s-1")
    )


def _score_T_cube(cube):
    score = 0
    if cube.standard_name == "air_temperature":
        score += 3
    if cube.var_name and "temp" in cube.var_name.lower():
        score += 2
    if "temperature" in cube.name().lower():
        score += 1
    return score


def _score_p_cube(cube):
    score = 0
    if cube.standard_name == "air_pressure":
        score += 3
    if cube.var_name:
        v = cube.var_name.lower()
        if v == "barometric_pressure":
            score += 3
        elif "press" in v:
            score += 2
    if cube.name() and "pressure" in cube.name().lower():
        score += 1

    return score


def _score_covar_cube(cube):
    score = 0
    text = " ".join(
        str(x).lower()
        for x in [cube.var_name, cube.standard_name, cube.long_name, cube.name()]
        if x
    )
    if "cov" in text:
        score += 2
    if "wt" in text or "w't" in text:
        score += 2
    return score


def sensible_heat_flux_from_covariance(cubes, **kwargs):
    """
    Convert turbulent temperature covariance into sensible heat flux.

    This operator computes surface upward sensible heat flux (SHF) from
    turbulent temperature covariance using:
        SHF = ρ * CPD * (w'T')
    where:
        ρ   = air density (derived from pressure and temperature)
        CPD  = specific heat capacity of dry air
        w'T' = covariance between vertical wind and temperature fluctuations
    The operator identifies the required input cubes from a collection
    based on their physical units, with optional use of metadata (e.g.
    standard names, variable names, long names) to resolve ambiguities.

    Specifically, it attempts to identify:
      - one covariance cube with units compatible with temperature × velocity
        (e.g. "K m s-1" or "degC m s-1")
      - one air temperature cube (units convertible to "K" or "degC")
      - one pressure cube (units convertible to "Pa")

    If multiple plausible candidates exist for a given role, a scoring
    system based on metadata is used to select the most likely match.
    If ambiguity remains after scoring, a ValueError is raised.

    Parameters
    ----------
    cubes : iris.cube.Cube or iterable of Cube
        Collection of input cubes. Must contain exactly one physically
        plausible cube for each of:
            - temperature covariance (w'T')
            - air temperature
            - air pressure
        Additional cubes are passed through unchanged.

    **kwargs : dict, optional
        Optional keyword arguments.
        HEIGHT : float or int
            Nominal measurement height (in metres), used only for
            metadata annotation of the output cube.

    Returns
    -------
    iris.cube.Cube or iris.cube.CubeList
        Output cubes where:
        - Input cubes used in the SHF calculation are removed
        - A new cube is added:
            surface_upward_sensible_heat_flux [W m-2]
        - All other input cubes are passed through unchanged

        If only the SHF cube remains, a single Cube is returned.
        Otherwise, a CubeList is returned.

    Assumptions and Notes
    ---------------------
    - Input cubes are assumed to be on a consistent grid; no spatial
      alignment or regridding is performed.
    - Temperature is internally converted to Kelvin; pressure is converted
      to Pascals.
    - Temperature covariance may be expressed in either "degC m s-1" or
      "K m s-1". These are treated as numerically equivalent for turbulent
      fluctuations (i.e. offsets cancel in fluctuations).
    - No attempt is made to distinguish between resolved and turbulent
      flux components beyond unit consistency.
    - Identification of cubes is primarily unit-based; metadata is used
      only to resolve ambiguity between multiple candidates.

    Raises
    ------
    ValueError
        If required inputs (pressure, temperature, or covariance) cannot
        be uniquely identified from the provided cubes.
    """
    from cf_units import Unit

    cubes = (
        iris.cube.CubeList(cubes)
        if not isinstance(cubes, iris.cube.CubeList)
        else cubes
    )

    p_cand = [c for c in cubes if _is_p_cube(c)]
    T_cand = [c for c in cubes if _is_T_cube(c)]
    covar_cand = [c for c in cubes if _is_wt_covar_cube(c)]

    # Optional: use scoring if more than one candidate exists
    if len(p_cand) > 1:
        p_cand = sorted(p_cand, key=_score_p_cube, reverse=True)
        if len(p_cand) > 1 and _score_p_cube(p_cand[0]) == _score_p_cube(p_cand[1]):
            raise ValueError("Multiple plausible pressure cubes found")

    if len(T_cand) > 1:
        T_cand = sorted(T_cand, key=_score_T_cube, reverse=True)
        if len(T_cand) > 1 and _score_T_cube(T_cand[0]) == _score_T_cube(T_cand[1]):
            raise ValueError("Multiple plausible temperature cubes found")

    if len(covar_cand) > 1:
        covar_cand = sorted(covar_cand, key=_score_covar_cube, reverse=True)
        if len(covar_cand) > 1 and _score_covar_cube(
            covar_cand[0]
        ) == _score_covar_cube(covar_cand[1]):
            raise ValueError("Multiple plausible covariance cubes found")

    pressure = _exactly_one(p_cand[:1], "pressure")
    temp = _exactly_one(T_cand[:1], "temperature")
    wT = _exactly_one(covar_cand[:1], "w'T' covariance")

    temp_K = temp.copy()
    if temp_K.units.is_convertible(Unit("degC")):
        temp_K.convert_units("K")

    pres_Pa = pressure.copy()
    pres_Pa.convert_units("Pa")

    # Treat degC covariance numerically as K covariance for fluctuations
    wT_cov = wT.copy()
    if str(wT_cov.units) == "degC m s-1":
        wT_cov.units = Unit("K m s-1")

    rho_air = pres_Pa / (RD * temp_K)

    shf = wT_cov.copy()
    shf = CPD * rho_air * wT_cov
    shf.units = Unit("W m-2")
    shf.rename("surface_upward_sensible_heat_flux")
    shf.var_name = "surface_upward_sensible_heat_flux"

    used_ids = {id(wT), id(temp), id(pressure)}
    out = iris.cube.CubeList(c for c in cubes if id(c) not in used_ids)
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
