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


def sensible_heat_units(cubes, **kwargs):
    """
    Convert covariance measurements into surface upward sensible heat flux.

    This operator computes sensible heat flux (SHF) from turbulent covariance
    measurements using:
        SHF = ρ * Cp * (w'T')
    where:
        ρ   = air density (derived from pressure and temperature)
        Cp  = specific heat capacity of dry air
        w'T' = vertical wind–temperature covariance

    Parameters
    ----------
    cubes : iris.cube.Cube or iterable of Cube
        Collection of input cubes. Must include exactly one cube for each of:
            - wt_covariance_*
            - air_temperature_rtd_*
            - pressure_barometric
        Other cubes are passed through unchanged.

    kwargs : dict
        Must contain:
            WT_VARNAMES : str
                Comma-separated list of variable names to extract from `cubes`.
                Expected to include the three required inputs.
        Optional:
            HEIGHT : float or int
                Nominal height used for metadata tagging only (not used in computations).

    Returns
    -------
    iris.cube.Cube or iris.cube.CubeList
        Output cubes with:
            - All non-WT related cubes passed through unchanged
            - One additional cube:
                surface_upward_sensible_heat_flux[W m-2]

        Returns a single Cube if input was a single Cube, otherwise a CubeList.

    Assumptions and Notes
    ---------------------
    - Input cubes must be preselected so that exactly one of each required variable
      is present. No disambiguation is performed within this function.
    - Measurement heights of inputs may differ; these are recorded in output metadata.
    - The `HEIGHT` kwarg is treated as a nominal reporting height only and does not
      affect the calculation.
    - Units are normalised internally:
        - Temperature → K (defaults to degC if unknown)
        - Pressure → Pa (defaults to hPa if unknown)

    Raises
    ------
    ValueError
        If required inputs are missing or WT_VARNAMES is not provided.
    """
    from cf_units import Unit

    Cp = 1004.67  # J kg-1 K-1
    Rd = 287.05  # J kg-1 K-1
    cubes = (
        iris.cube.CubeList(cubes)
        if not isinstance(cubes, iris.cube.CubeList)
        else cubes
    )

    # --- Extract inputs explicitly listed upstream ---
    if "WT_VARNAMES" not in kwargs:
        raise ValueError("sensible_heat_units requires WT_VARNAMES")

    wanted = set(kwargs["WT_VARNAMES"].split(","))
    selected = {c.var_name: c for c in cubes if c.var_name in wanted}
    missing = wanted - set(selected)
    if missing:
        raise ValueError(f"sensible_heat_units missing inputs: {sorted(missing)}")

    wT = next(v for k, v in selected.items() if k.startswith("wt_covariance_"))
    temp = next(v for k, v in selected.items() if k.startswith("air_temperature_rtd_"))
    pressure = selected["pressure_barometric"]

    # --- Unit handling ---
    temp_K = temp.copy()
    if temp_K.units is None or temp_K.units.is_unknown():
        temp_K.units = Unit("degC")
    temp_K.convert_units("K")

    pres_Pa = pressure.copy()
    if pres_Pa.units is None or pres_Pa.units.is_unknown():
        pres_Pa.units = Unit("hPa")
    pres_Pa.convert_units("Pa")

    # --- Compute sensible heat flux ---
    rho_air = pres_Pa.data / (Rd * temp_K.data)
    shf = wT.copy()
    shf.data = Cp * rho_air * wT.data
    shf.units = "W m-2"
    shf.rename("surface_upward_sensible_heat_flux")
    shf.var_name = "surface_upward_sensible_heat_flux"

    # --- Metadata: be explicit about mixed heights ---
    shf.attributes["model_name"] = wT.attributes.get("model_name")
    shf.attributes["measurement_heights"] = {
        "wt_covariance": wT.var_name.split("_")[-1],
        "air_temperature": temp.var_name.split("_")[-1],
        "air_pressure": "1.2 m",
    }
    if "HEIGHT" in kwargs:
        shf.attributes["nominal_height"] = f"{kwargs['HEIGHT']} m"

    # --- Return: passthrough everything except inputs, plus SHF ---
    out = iris.cube.CubeList(c for c in cubes if c.var_name not in wanted)
    out.append(shf)
    return out if len(out) > 1 else out[0]
