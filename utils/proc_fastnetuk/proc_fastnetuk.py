#!/usr/bin/python3

"""Fix FastNetUK inference data on UGRID with limited metadata.

For more information on this script and how to use it, see the README.md
"""

import argparse
import re
from glob import glob

import iris
import iris.coord_systems
import iris.coords as icoords
import iris.cube
import numpy as np
from cf_units import Unit

# Lookup dictionary to translate to LFRic long_names.
UGRID_VAR_LOOKUP = {
    "t": {"long_name": "temperature_at_pressure_levels", "units": "K"},
    "u": {"long_name": "zonal_wind_at_pressure_levels", "units": "m s-1"},
    "v": {"long_name": "meridional_wind_at_pressure_levels", "units": "m s-1"},
    "w": {"long_name": "vertical_wind_at_pressure_levels", "units": "m s-1"},
    "q": {
        "long_name": "vapour_specific_humidity_at_pressure_levels_for_climate_averaging",
        "units": "kg kg-1",
    },
    "z": {"long_name": "geopotential_height_at_pressure_levels", "units": "m"},
    "sp": {"long_name": "surface_air_pressure", "units": "Pa"},
    "10u": {"long_name": "eastward_wind_at_10m", "units": "m s-1"},
    "10v": {"long_name": "northward_wind_at_10m", "units": "m s-1"},
    "lsm": {"long_name": "land_binary_mask", "units": "1"},
    "2t": {"long_name": "temperature_at_screen_level", "units": "K"},
    "2d": {"long_name": "dew_point_temperature_at_screen_level", "units": "K"},
    "skt": {"long_name": "grid_surface_temperature", "units": "K"},
    "tp": {"long_name": "surface_microphysical_rainfall_rate", "units": "mm 6hr-1"},
    "latitude": {"long_name": "latitude", "units": "degrees"},
    "longitude": {"long_name": "longitude", "units": "degrees"},
}


def rebuild_metadata(cube, grid):
    """
    Rebuild iris cube metadata.

    The cube will have metadata within its name and an additional pressure auxiliary
    coordinate inferred from the cube name if present.

    Parameters
    ----------
    cube: iris.cube.Cube
        Original unstructured source cube, used for fixing metadata.
    grid: iris.cube.Cube
        An iris cube, containing latitude/longitude coordinates of the
        UKV mesh.

    Returns
    -------
    iris.cube.Cube
        A structured iris cube with appropriate metadata.
    """
    # Determine if cube matches certain string pattern.
    match = re.match(
        r"^([a-zA-Z][a-zA-Z0-9]*|\d+[a-zA-Z]+)(?:_(\d+))?$",
        cube.name(),
    )

    if match is None:
        return None

    # Extract var and pressure, if present.
    var_key, pressure_hpa = match.groups()

    # See if there is an entry for the variable, if not return.
    meta = UGRID_VAR_LOOKUP.get(var_key)

    if meta is None:
        return None

    # Get latitude, longitude coordinate objects.
    lat_coord = grid.coord("grid_latitude")
    lon_coord = grid.coord("grid_longitude")

    # Create time dimensions, including forecast_period and forecast_reference_time.
    time_coord = cube.coord("time")

    base_time_units = Unit("hours since 1970-01-01 00:00:00")
    frt_point = base_time_units.date2num(
        time_coord.units.num2date(time_coord.points[0])
    )

    forecast_reference_time = icoords.DimCoord(
        [frt_point],
        standard_name="forecast_reference_time",
        units=base_time_units,
    )

    forecast_period = icoords.DimCoord(
        (time_coord.points - time_coord.points[0]) / 3600,
        standard_name="forecast_period",
        units="hours",
    )

    # Start with coordinates of forecast_reference_time and forecast_period.
    coords = [
        (forecast_reference_time, 0),
        (forecast_period, 1),
    ]

    # Reshape cube to standard UKV. This is hard-coded, as this script only
    # supports UKV data.
    cube_data = cube.data.reshape(cube.shape[0], 808, 621)

    # If pressure exists, create additional size 1 dimension for future concatenation.
    if pressure_hpa is not None:
        pressure_coord = icoords.DimCoord(
            [int(pressure_hpa)],
            long_name="pressure",
            units="hPa",
        )

        cube_data = cube_data[np.newaxis, :, np.newaxis, :, :]

        coords.extend(
            [
                (pressure_coord, 2),
                (lat_coord, 3),
                (lon_coord, 4),
            ]
        )

    # If pressure doesn't exist, just use latitude/longitude in addition to time.
    else:
        cube_data = cube_data[np.newaxis, :, :, :]
        coords.extend(
            [
                (lat_coord, 2),
                (lon_coord, 3),
            ]
        )

    # Create cube with coordinates
    out_cube = iris.cube.Cube(
        cube_data,
        dim_coords_and_dims=coords,
    )

    # Add auxcoord time coordinate that varies with forecast_period and forecast_reference_time.
    time_data = base_time_units.date2num(time_coord.units.num2date(time_coord.points))
    time_data = time_data[np.newaxis, :]
    out_cube.add_aux_coord(
        iris.coords.AuxCoord(
            time_data,
            standard_name="time",
            units=base_time_units,
        ),
        data_dims=(0, 1),
    )

    # Add metadata for long name, units, and preserve other attributes.
    out_cube.rename(meta["long_name"])
    out_cube.long_name = meta["long_name"]
    out_cube.units = meta["units"]

    out_cube.attributes = cube.attributes.copy()

    # Delete fill value attribute if exists, as this tends to be np.float64(nan), which causes iris merge/concat issues.
    if "fill_value" in out_cube.attributes:
        del out_cube.attributes["fill_value"]

    # Some data corrections for specific variables with certain units.
    if out_cube.long_name == "geopotential_height_at_pressure_levels":
        out_cube.data /= 9.81
        out_cube.units = "m"

    # Convert meters to mm.
    elif out_cube.long_name == "surface_microphysical_rainfall_rate":
        out_cube.data *= 1000.0

    return out_cube


def main() -> None:
    """
    Define and parse input and output path arguments.

    Run processing on FastNetUK data.

    Process produces CSET-ready netCDF files for loading.
    """
    parser = argparse.ArgumentParser(description="Process arguments.")
    parser.add_argument("--inputpath", required=True, help="Path to file(s) to load.")
    parser.add_argument(
        "--outputpath",
        type=str,
        required=True,
        help="Path to save final output data.",
    )

    args = parser.parse_args()

    # Get file paths
    inputpath = args.inputpath
    outputpath = args.outputpath + "/"

    # Load mask containing lat/lon to project onto.
    ukv_mask = iris.load_cube("ukv_mesh.nc")

    for file in glob(inputpath):
        print(f"Running script on {file}")

        # Load data and restructure.
        cubes = iris.load(file)

        fixed_cubes = iris.cube.CubeList()
        # For each cube, where ndim > 1 (excluding latitude/longitude array), do regridding
        # on array, and correct metadata.
        for cube in cubes:
            if cube.ndim > 1:
                print(f"Fixing {cube.name()}")
                cube = rebuild_metadata(cube, ukv_mask)
                if cube:
                    fixed_cubes.append(cube)

        print("Saving restructured cubes")
        iris.save(
            fixed_cubes.concatenate(), f"{outputpath}/fixed_{file.split('/')[-1]}"
        )
        print(f"Done file {file}")


if __name__ == "__main__":
    main()
