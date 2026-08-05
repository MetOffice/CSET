"""Script to process AIFS grib data to netCDF for CSET.

Please see README.md for more information how to run this script.
"""

import argparse
import os
import re
import subprocess
from glob import glob

import iris
import numpy as np
from iris.coords import DimCoord
from iris.cube import CubeList


def fix_name_and_units(cube):
    """Fix AIFS name and units, where relevant.

    Parameters
    ----------
    cube: iris.Cube
        An iris cube to have its metadata modified.

    Returns
    -------
    cube: iris.Cube
        An iris cube that has updated names and units that CSET can understand.
    """
    # Lookup dictionary for AIFS names to be converted to LFRic long names, and unit change,
    # where necessary.
    aifs_to_lfric_dict = {
        "2 metre dewpoint temperature": ["dew_point_temperature_at_screen_level", None],
        "Skin temperature": ["grid_surface_temperature", None],
        "Snowfall water equivalent": ["grid_surface_snow_amount", None],
        "Surface long-wave (thermal) radiation downwards": [
            "surface_downward_clear_longwave_flux_radiative_timestep",
            None,
        ],
        "Total Cloud Cover": ["area_cloud_fraction", None],
        "Total Precipitation": ["surface_precipitation_amount", None],
        "Total column water": ["atmosphere_mass_content_of_water_vapor", None],
        "Mean sea level pressure": ["air_pressure_at_mean_sea_level", None],
        "2 metre temperature": ["temperature_at_screen_level", None],
        "Temperature": ["temperature_at_pressure_levels", None],
        "10 metre U wind component": ["eastward_wind_at_10m", None],
        "10 metre V wind component": ["northward_wind_at_10m", None],
        "U component of wind": ["zonal_wind_at_pressure_levels", None],
        "V component of wind": ["meridional_wind_at_pressure_levels", None],
        "Geopotential": ["geopotential_height_at_pressure_levels", "m"],
        "Vertical velocity": ["vertical_wind_at_pressure_levels", None],
        "Specific humidity": [
            "vapour_specific_humidity_at_pressure_levels_for_climate_averaging",
            None,
        ],
        "Surface pressure": ["surface_air_pressure", None],
        "Surface short-wave (solar) radiation downwards": [
            "surface_direct_shortwave_flux_radiative_timestep",
            None,
        ],
    }

    # Get cube long name.
    long_name = cube.long_name

    # If cube long name in dict, then get new name/units.
    if long_name in aifs_to_lfric_dict:
        new_name, new_units = aifs_to_lfric_dict[long_name]

        # Update long_name and cube name (ignore standard_name as this is not used).
        cube.long_name = new_name
        cube.rename(new_name)

        # Convert units if required.
        if new_units is not None:
            # Exception for geopotential height, as iris cannot directly convert.
            if str(cube.units) == "m**2 s**-2" and str(new_units) == "m":
                cube = cube.copy(data=cube.lazy_data() / 9.80665)
                cube.units = "m"
            else:
                cube.convert_units(new_units)

    return cube


def fix_ensemble_cubes(cubes):
    """
    Fix ensemble dimension in cube list.

    The ensemble dimension is present in some cubes, as an auxiliary coordinate, where the
    control members do not have this dimension. This function ensures each cube has a
    realization coordinate, where the control member is member 0, so the cubes can be concatenated.

    Parameters
    ----------
    cubes: iris.cube.CubeList
        A cubelist containing all cubes loaded from the AIFS ensemble.

    Returns
    -------
    processed: iris.cube.CubeList
        A cubelist containing the corrected cubes.

    """
    # Cubelist to store corrected cubes.
    processed = CubeList()

    for cube in cubes:
        cube = cube.copy()

        # Remove attributes that prevent concatenation
        cube.attributes.pop("history", None)

        # Correction for cubes that contain a pressure_level coord that is not DimCoord.
        if cube.coords("pressure_level"):
            pressure_coord = cube.coord("pressure_level")

            # If a pressure_level coordinate does not exist as a DimCoord, create it, ensure ordered monotonically.
            if not isinstance(pressure_coord, DimCoord):
                pressure_dim = cube.coord_dims(pressure_coord)[0]

                # Sort pressure values
                order = np.argsort(pressure_coord.points)
                sorted_points = pressure_coord.points[order]

                # Reorder data to match
                cube.data = np.take(cube.core_data(), order, axis=pressure_dim)

                # Replace aux coord with dim coord
                cube.remove_coord("pressure_level")

                cube.add_dim_coord(
                    DimCoord(
                        sorted_points,
                        long_name=pressure_coord.long_name,
                        standard_name=pressure_coord.standard_name,
                        var_name=pressure_coord.var_name,
                        units=pressure_coord.units,
                        attributes=pressure_coord.attributes,
                    ),
                    pressure_dim,
                )

        # Perturbed members have an ensemble_member coord.
        if cube.coords("ensemble_member"):
            cube.remove_coord("ensemble_member")

            # Hard coded, as AIFS supported has 50 perturbed members.
            realization_coord = DimCoord(
                np.arange(1, 51),
                standard_name="realization",
                units="1",
            )

            # ensemble member dimension is dimension 1
            cube.add_dim_coord(realization_coord, 1)

        # Control member
        else:
            # Add a new dimension of length 1
            cube = iris.util.new_axis(cube)

            # Create new realization coordinate
            realization_coord = DimCoord(
                [0],
                standard_name="realization",
                units="1",
            )

            # new_axis inserts the dimension at position 0 as standard.
            cube.add_dim_coord(realization_coord, 0)

            # Always move realization after time
            order = list(range(cube.ndim))
            order[0], order[1] = order[1], order[0]
            cube.transpose(order)

        processed.append(cube)

    # Combine control and perturbed cubes now that they share a common realization axis.
    processed = processed.concatenate()

    return processed


def fix_time_and_meta(cubes):
    """
    Fix time coordinates and adjust metadata such as names and units.

    Make the data CSET compliant by creating a forecast_period dimension,
    and adding valid time as a time auxiliary coordinate, and a forecast_reference_time
    as a scalar coordinate.

    Parameters
    ----------
    cubes: iris.cube.CubeList
        A cubelist of cubes to fix time and metadata.

    Returns
    -------
    done_cubes: iris.cube.CubeList
        A cubelist of cubes that have been fixed.
    """
    # Create empty cubelist to store fixed cubes
    done_cubes = iris.cube.CubeList()

    for cube in cubes:
        # Get a copy of time coord
        time_coord = cube.coord("time")

        # Forecast periods relative to initialisation, which is taken as
        # the first time in the file. We have to make this assumption, as AIFS
        # grib has no information on model initialisation (or at least is lost
        # in the netCDF translation step).
        fp_points = time_coord.points - time_coord.points[0]

        # Work out units of forecast_period and adjust if necessary below.
        units_str = str(time_coord.units)

        if units_str.startswith("seconds since"):
            fp_points = fp_points / 3600.0
            fp_units = "hours"
        elif units_str.startswith("minutes since"):
            fp_points = fp_points / 60.0
            fp_units = "hours"
        elif units_str.startswith("hours since"):
            fp_units = "hours"
        else:
            raise ValueError(f"Unhandled time units: {time_coord.units}")

        # Get copy of time coordinate, and dimension axis corresponding to time.
        time_coord_points = time_coord.points.copy()
        time_dim = cube.coord_dims("time")[0]

        # Create forecast period dimension
        fp_coord = iris.coords.DimCoord(
            fp_points,
            standard_name="forecast_period",
            units=fp_units,
        )

        # Remove time dimension temporarily, as forecast_period will be lead dimension
        cube.remove_coord("time")
        cube.add_dim_coord(fp_coord, time_dim)

        # Add auxiliary forecast initialisation dimension
        cube.add_aux_coord(
            iris.coords.AuxCoord(
                time_coord_points[0],
                standard_name="forecast_reference_time",
                units=time_coord.units,
            )
        )

        # Create auxiliary time dimension of valid time.
        new_time_coord = iris.coords.AuxCoord(
            time_coord_points,
            standard_name="time",
            units=time_coord.units,
        )

        # Add this dimension to the cube, tied to the forecast_period dimension.
        cube.add_aux_coord(
            new_time_coord,
            data_dims=(cube.coord_dims("forecast_period")[0],),
        )

        # Fix cube long_name, name and units.
        cube = fix_name_and_units(cube)

        # Append slice to cutout list.
        done_cubes.append(cube)

        print(f"{cube.name}...done.")

    return done_cubes


def run_in_shell_grib_tools(inputpath, outpath):
    """
    Split out grib messages into streams and convert to netCDF.

    This is required, as iris cannot load the grib data directly due to issues with
    some of the variables (fixed levels). ECCODES also produces an error if grib_to_netcdf
    is called on the file without splitting level types first. Here, we write to a hidden
    file in the output directory prior to iris metadata processing.

    Parameters
    ----------
    inputpath: str
        String input path, which can be globbed if wildcards are used.
    outpath: str
        Directory to write output.

    Returns
    -------
    None
    """
    # Iterate over all files supplied using glob
    for file in glob(inputpath):
        for typeOfLevel in [
            "isobaricInhPa",
            "heightAboveGround",
            "surface",
            "meanSea",
            "entireAtmosphere",
        ]:
            print(f"proc file {file} for typeOfLevel {typeOfLevel}")

            # Get file name by splitting directory and extension.
            name = os.path.splitext(os.path.basename(file))[0]

            # Initial step to extract particular level type.
            subprocess.check_output(
                [
                    "grib_copy",
                    "-w",
                    "typeOfLevel=" + typeOfLevel,
                    file,
                    outpath + "." + name + "_extract_" + typeOfLevel + ".grib2",
                ]
            )

            # Next step to convert to netCDF.
            subprocess.check_output(
                [
                    "grib_to_netcdf",
                    outpath + "." + name + "_extract_" + typeOfLevel + ".grib2",
                    "-o",
                    outpath + "." + name + "_extract_" + typeOfLevel + ".nc",
                ]
            )

            # Remove old grib file extracted as no longer needed.
            subprocess.check_output(
                ["rm", outpath + "." + name + "_extract_" + typeOfLevel + ".grib2"]
            )


def main():
    """
    Run processing on AIFS grib data.

    Process produces CSET-ready netCDF files for loading.
    """
    parser = argparse.ArgumentParser(description="Process arguments.")
    parser.add_argument("--inputpath", required=True, help="Path to file(s) to load.")
    parser.add_argument(
        "--forecastinit",
        type=str,
        required=True,
        help="Forecast initialisation to datestamp output.",
    )
    parser.add_argument(
        "--outpath",
        type=str,
        required=True,
        help="Path to save intermediate/final output data.",
    )

    args = parser.parse_args()

    # Populate required variables
    inputpath = args.inputpath
    forecastinit = args.forecastinit
    outpath = args.outpath + "/"

    print()
    print("Starting preproc_aifs.py...")
    print()
    print("Running preprocess with grib_copy and grib_to_netcdf")
    run_in_shell_grib_tools(inputpath, outpath)

    cubes = fix_ensemble_cubes(iris.load(outpath + "/.*.nc"))
    cubes = fix_time_and_meta(cubes)

    # Save each variable, otherwise end up with huge 100GBs files.
    for cube in cubes:
        # Sanitise name in case not corrected to LFRic.
        safe_name = cube.name().replace(" ", "_")
        safe_name = re.sub(r"[()]", "", safe_name)

        iris.save(cube, outpath + "/AIFS_" + forecastinit + "_" + safe_name + ".nc")

    for f in glob(outpath + "/.*.nc"):
        os.remove(f)

    print("Done!")


if __name__ == "__main__":
    main()
