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
from scipy.interpolate import LinearNDInterpolator

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


def rebuild_metadata(cube, arr, lat, lon):
    """
    Rebuild iris cube metadata.

    The cube will have metadata within its name and an additional pressure auxiliary
    coordinate inferred from the cube name if present.

    Parameters
    ----------
    cube : iris.cube.Cube
        Original unstructured source cube, used for fixing metadata.
    arr : np.ndarray
        Numpy array of restructured (2D) data.
    lat : np.ndarray
        1D latitude coordinate values of regridded data
    lon : np.ndarray
        1D longitude coordinate values of regridded data

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

    # Create latitude, longitude coordinate objects.
    lat_coord = icoords.DimCoord(
        lat,
        standard_name="latitude",
        units="degrees",
    )

    lon_coord = icoords.DimCoord(
        lon,
        standard_name="longitude",
        units="degrees",
    )

    # Create time dimensions, including forecast_period and forecast_reference_time.
    time_coord = cube.coord("time").copy()

    forecast_reference_time = icoords.AuxCoord(
        time_coord.points[0],
        standard_name="forecast_reference_time",
        units=time_coord.units,
    )

    forecast_period = icoords.DimCoord(
        (time_coord.points - time_coord.points[0]) / 3600,
        standard_name="forecast_period",
        units="hours",
    )

    # Start with coordinates of just forecast_period.
    coords = [
        (forecast_period, 0),
    ]

    # If pressure exists, create additional size 1 dimension for future concatenation.
    if pressure_hpa is not None:
        pressure_coord = icoords.DimCoord(
            [int(pressure_hpa)],
            long_name="pressure",
            units="hPa",
        )

        arr = arr[:, np.newaxis, :, :]

        coords.extend(
            [
                (pressure_coord, 1),
                (lat_coord, 2),
                (lon_coord, 3),
            ]
        )

    # If pressure doesn't exist, just use latitude/longitude in addition to time.
    else:
        coords.extend(
            [
                (lat_coord, 1),
                (lon_coord, 2),
            ]
        )

    # Create cube with coordinates
    out_cube = iris.cube.Cube(
        arr,
        dim_coords_and_dims=coords,
    )

    # Add scalar time coordinates
    out_cube.add_aux_coord(forecast_reference_time)
    out_cube.add_aux_coord(time_coord, data_dims=(0,))

    # Add metadata for long name, units, and preserve other attributes.
    out_cube.rename(meta["long_name"])
    out_cube.long_name = meta["long_name"]
    out_cube.units = meta["units"]

    out_cube.attributes = cube.attributes.copy()

    # Some unit corrections for specific variables.
    if out_cube.long_name == "geopotential_height_at_pressure_levels":
        out_cube.data /= 9.81

    elif out_cube.long_name == "surface_microphysical_rainfall_rate":
        out_cube.data *= 1000.0

    return out_cube


def ugrid_transform(arr, tri, lat_grid, lon_grid, xy):
    """
    Restructure a flattened/unstructured cube.

    Parameters
    ----------
    arr : arrayy
        An iris cube to restructure.
    tri : scipy.spatial._qhull.Delaunay
        A scipy object containing the triangulation mapping of cell points.
    lat_grid : np.ndarray
        1D latitude coordinate values of target grid.
    lon_grid : np.ndarray
        1D longitude coordinate values of target grid.
    xy : np.ndarray
        Meshed and flattened target grid points.

    Returns
    -------
    iris.cube.Cube
        A structured iris cube with appropriate metadata.

    Notes
    -----
    This function uses a pre-calculated triangulation, to save rebuilding for
    every cube. This therefore assumes all cubes being restructured have the
    same flattened structure.
    """
    # Create empty numpy array to store regridded data.
    out = np.empty((arr.shape[0], lat_grid.size, lon_grid.size))

    # Extract and transpose source data values.
    src_vals = arr.T

    # Build linear interpolator object mapping target triangulation to source values.
    interp = LinearNDInterpolator(tri, src_vals)

    # Interpolate values onto target grid using linear interpolation.
    out_flat = interp(xy)

    # Transpose, and reshape to target 2D regular lat/lon grid.
    out = out_flat.T.reshape(arr.shape[0], lat_grid.size, lon_grid.size)

    return out


def fix_cubes(cubes):
    """
    Restructure ugrid cubes and then fix metadata.

    First, fixes cube metadata names as a first fix, and then regrids, and then
    finally adds metadata associated with new coordinates.

    Parameters
    ----------
    cubes : iris.cube.CubeList
        A cubelist containing unstructured cubes, along with cubes containing
        latitude and longitude information.

    Returns
    -------
    fixed_cubes: iris.cube.CubeList
        A list of iris cubes, that have been restructured onto a regular grid,
        with appropriate corrections to metadata.

    Notes
    -----
    Currently, data is regridded to a 0.02degree rectilinear grid. This is because
    there is no metada in the source file that describes the target resolution
    of what it should be regridded to.
    """
    # First, extract latitude and longitude coordinates
    lat = cubes.extract("latitude")[0].data
    lon = cubes.extract("longitude")[0].data
    points = np.column_stack((lon, lat))

    # Create output mesh, using standard grid ~2km resolution
    # TODO: discussions with ML developers to include metadata so
    # we don't have to guess target lat/lon resolution.
    lon_grid = np.arange(lon.data.min(), lon.data.max(), 0.02)
    lat_grid = np.arange(lat.data.min(), lat.data.max(), 0.02)
    Lon2d, Lat2d = np.meshgrid(lon_grid, lat_grid)

    # Flatten target points
    xy = np.column_stack((Lon2d.ravel(), Lat2d.ravel()))

    # Build triangulation via a dummy interpolator
    tri_interp = LinearNDInterpolator(points, np.zeros(points.shape[0]))
    tri = tri_interp.tri

    fixed_cubes = iris.cube.CubeList()

    # For each cube, where ndim > 1 (excluding latitude/longitude array), do regridding
    # on array, and correct metadata.
    for cube in cubes:
        if cube.ndim > 1:
            print(f"Fixing {cube.name()}")
            result_arr = ugrid_transform(cube.data, tri, lat_grid, lon_grid, xy)
            cube = rebuild_metadata(cube, result_arr, lat_grid, lon_grid)
            if cube:
                fixed_cubes.append(cube)

    return fixed_cubes.concatenate()


def main() -> None:
    """
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

    for file in glob(inputpath):
        print(f"Running script on {file}")

        # Load data and restructure.
        cubes = iris.load(file)
        cubes = fix_cubes(cubes)

        print("Saving restructured cubes")
        iris.save(cubes, f"{outputpath}/fixed_{file.split('/')[-1]}")
        print(f"Done file {file}")


if __name__ == "__main__":
    main()
