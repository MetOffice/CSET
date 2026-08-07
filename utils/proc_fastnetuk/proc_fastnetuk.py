"""TODO"""

import iris
import iris.coord_systems
import iris.coords as icoords
import iris.cube
import numpy as np
from scipy.interpolate import LinearNDInterpolator
from iris.analysis.cartography import rotate_pole
import argparse
from glob import glob


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


def _rebuild_ugrid_meta_firstfix(cube):
    """
    Rebuild iris cube metadata.

    The cube will have metadata within its name and an additional pressure auxiliary
    coordinate inferred from the cube name if present.

    Parameters
    ----------
    cube : iris.cube.Cube
        Original unstructured source cube, used for fixing metadata.

    Returns
    -------
    iris.cube.Cube
        A structured iris cube with appropriate metadata.
    """
    # Get original cube time coordinate dimension.
    try:
        time_coord = cube.coord("time")
    except iris.exceptions.CoordinateNotFoundError:
        return None

    # Create new ugrid coordinate placeholder.
    #  ugrid_coord = icoords.DimCoord(np.arange(cube.shape[1]))

    # Parse cube name, to determine if it contains a likely pressure variable/level.
    # If it can't parse this pattern, returns None
    m = re.match(r"^([a-zA-Z][a-zA-Z0-9]*|\d+[a-zA-Z]+)(?:_(\d+))?$", cube.name())

    # Extract variable and pressure from cube name components.
    # If it can't find, returns None.
    var_key, pressure_hpa = m.group(1), m.group(2)

    # Rename cube using lookup dictionary, if a lookup exists.
    meta = UGRID_VAR_LOOKUP.get(var_key)

    if meta is None:
        return
    else:
        # If there is a number in cube name that can be split.
        if pressure_hpa is not None:
            # Create new pressure coordinate dimension.
            pressure_coord = icoords.DimCoord(
                [int(pressure_hpa)],
                long_name="pressure",
                units="hPa",
            )

            # If ndim = 1, a single 2D timeslice with pressure and time.
            if cube.ndim == 1:
                arr = cube.core_data()[np.newaxis, np.newaxis, :]
            else:
                arr = cube.core_data()[:, np.newaxis, :]

            out_cube = iris.cube.Cube(
                arr,
                dim_coords_and_dims=[
                    (time_coord, 0),
                    (pressure_coord, 1),
                    (icoords.DimCoord(np.arange(arr.shape[-1])), 2),
                ],
            )

        else:
            # Not a pressure level variable, so only 3 dimensions.
            # If ndim = 1, a single 2D timeslice withd time.
            if cube.ndim == 1:
                arr = cube.core_data()[np.newaxis, :]
            else:
                arr = cube.core_data()

            out_cube = iris.cube.Cube(
                arr,
                dim_coords_and_dims=[
                    (time_coord, 0),
                    (icoords.DimCoord(np.arange(arr.shape[-1])), 1),
                ],
            )

        # Fix cube metadata
        out_cube.long_name = meta["long_name"]
        out_cube.units = meta["units"]
        out_cube.rename(meta["long_name"])

        # Add forecast reference time as 'time_origin' to mimic lfric where it will
        # reconstruct forecast_period in a later callback.
        # Extract the origin string from the units
        time_origin = time_coord.units.origin

        # Strip the "seconds since " part.
        time_origin = time_origin.split("since ")[1]

        # Add to cube attributes as str.
        out_cube.coord("time").attributes["time_origin"] = time_origin

    return out_cube



def _rebuild_ugrid_meta(cube, arr, lat, lon):
    """
    Rebuild iris cube metadata.

    The cube will have metadata within its name and an additional pressure auxiliary
    coordinate inferred from the cube name if present.

    Parameters
    ----------
    cube : iris.cube.Cube
        Original unstructured source cube, used for fixing metadata.
    arr : np.ndarray
        Numpy array of UGRID data.
    lat : np.ndarray
        1D latitude coordinate values of regridded data
    lon : np.ndarray
        1D longitude coordinate values of regridded data

    Returns
    -------
    iris.cube.Cube
        A structured iris cube with appropriate metadata.
    """
    # Create new latitude coordinate.
    lat_coord = icoords.DimCoord(
        lat,
        standard_name="latitude",
        units="degrees",
    )

    # Create new longitude coordinate.
    lon_coord = icoords.DimCoord(
        lon,
        standard_name="longitude",
        units="degrees",
    )

    # Get original cube time coordinate dimension.
    time_coord = cube.coord("time")

    try:
        pressure_coord = cube.coord("pressure")
    except iris.exceptions.CoordinateNotFoundError:
        pressure_coord = None

    if pressure_coord is not None:
        # Create length 1 axis to match shape for pressure
        arr = arr[:, np.newaxis, :, :]

        # Create new cube with these dimensions.
        out_cube = iris.cube.Cube(
            arr,
            dim_coords_and_dims=[
                (time_coord, 0),
                (pressure_coord, 1),
                (lat_coord, 2),
                (lon_coord, 3),
            ],
        )

    else:
        out_cube = iris.cube.Cube(
            arr,
            dim_coords_and_dims=[
                (time_coord, 0),
                (lat_coord, 1),
                (lon_coord, 2),
            ],
        )

    # Set units/cube name from previous constructed cube.
    out_cube.standard_name = cube.standard_name
    out_cube.long_name = cube.long_name
    out_cube.units = cube.units

    # Copy attributes.
    out_cube.attributes = cube.attributes.copy()

    # Change units, geopot in m2 s-2.
    if out_cube.long_name == "geopotential_height_at_pressure_levels":
        out_cube.data = out_cube.data / 9.81

    # Raw data in units of 6h accum in meters.
    if out_cube.long_name == "surface_microphysical_rainfall_rate":
        out_cube.data = out_cube.data * 1000.0

    return out_cube


def _restructure_ugrid_regrid(cube, tri, lat_grid, lon_grid, xy):
    """
    Restructure a flattened/unstructured cube.

    Parameters
    ----------
    cube : iris.cube
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
    out = np.empty((cube.shape[0], lat_grid.size, lon_grid.size))

    logging.debug(f"Interpolating {cube.name()}")

    # Extract and transpose source data values.
    src_vals = cube.data.T

    # Build linear interpolator object mapping target triangulation to source values.
    interp = LinearNDInterpolator(tri, src_vals)

    # Interpolate values onto target grid using linear interpolation.
    out_flat = interp(xy)

    # Transpose, and reshape to target 2D regular lat/lon grid.
    out = out_flat.T.reshape(cube.shape[0], lat_grid.size, lon_grid.size)

    # Rebuild metadata using lookup table (mostly for anemoi ML models).
    out_cube = _rebuild_ugrid_meta(cube, out, lat_grid, lon_grid)

    # Return restructured cube with appropriate metadata
    return out_cube


def fix_metadata(cubes, constraint):
    """
    Pre-filter cubes prior to regridding to reduce excess compute.

    Parse cubes and filter for required variable, alongside latitude and
    longitude, for further processing. This reduces compute overhead on
    variables that we don't require. This also cleans metadata prior to filtering.

    Parameters
    ----------
    cubes : iris.cube.CubeList
        A cubelist containing unstructured cubes, along with cubes containing
        latitude and longitude information.

    constraint : iris.constraint
        Constraint in order to extract required variable.

    Returns
    -------
    filterd_cubes : iris.cube.CubeList
        A cubelist containing the required cube that matches the constraint, along
        with latitude and longitude cubes.
    """
    # Add metadata to variables, if appropriate
    sanitised_cubes = iris.cube.CubeList()
    for cube in cubes:
        out = _rebuild_ugrid_meta_firstfix(cube)
        if out is not None:
            sanitised_cubes.append(out)

    # Create empty cubelist.
    filtered_cubes = iris.cube.CubeList()

    # Extract latitude and longitude cubes, and append these to filtered_cubes.
    filtered_cubes.append(cubes.extract("latitude")[0])
    filtered_cubes.append(cubes.extract("longitude")[0])

    # Extract required cube based on constraint.
    for c in sanitised_cubes.extract(constraint):
        filtered_cubes.append(c)

    return filtered_cubes


def restructure_ugrid(cubes):
    """
    Restructure ugrid cubes using parallel processing.

    Parameters
    ----------
    cubes : iris.cube.CubeList
        A cubelist containing unstructured cubes, along with cubes containing
        latitude and longitude information.

    constraint: iris.Constraint
        An iris constraint (or combined constraint) to filter cubes on.

    Returns
    -------
    fixed_cubes: iris.cube.CubeList
        A list of iris cubes, that have been restructured onto a regular grid,
        with appropriate corrections to metadata.
    """
    # First, parse all cubes and fix their metadata (apart from latitude/longitude,
    # which we do later after regridding), and extract required variable from constraint.
    cubes = fix_metadata(cubes, constraint)

    # First, extract latitude and longitude coordinates
    lat = cubes.extract("latitude")[0].data
    lon = cubes.extract("longitude")[0].data
    points = np.column_stack((lon, lat))

    # Create output mesh, using standard grid ~2km resolution
    # TODO: discussions with ML developers to include metadata so
    # we don't have to guess target lat/lon resolution.
    # For now, we assume data no higher resolution than 2p2km.
    # This will have impacts on PDFs.
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
    # on array.
    for cube in cubes:
        if cube.ndim > 1:
            result_arr = _restructure_ugrid_regrid(cube, tri, lat_grid, lon_grid, xy)
            fixed_cubes.append(result_arr)

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

    inputpath = args.inputpath
    outputpath = args.outpath + "/"

    for file in glob(inputpath):
        print(f"Running script on {file}")

        # Func1: Load all cubes, get lat, lon
        cubes = iris.load(file)
        cubes = restructure_ugrid(cubes)
