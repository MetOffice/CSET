"""
Read Rainfields3 data into MET.

Use in grid_stat like:

    OBS_GRID_STAT_INPUT_TEMPLATE = PYTHON_NUMPY
    OBS_VAR1_NAME = /path/to/read_rainfields.py {valid?fmt=%Y%m%d_%H%M} {RADARID}

With RADARID being one of the identifiers from /g/data/rq0/level_1/odim_pvol/radar_site_list.csv

Data is output with variable name APCP_001500 and should be aggregated with
PCPCombine to the target accumulation before use.
"""

import argparse
from datetime import datetime
from tempfile import NamedTemporaryFile
from textwrap import dedent
from zipfile import ZipFile

import iris
import iris.cube
import numpy


def generate_target(source: iris.cube.Cube) -> iris.cube.Cube:
    """
    Generate a target Lambert Conformal grid for regridding.

    MET cannot accept an Albers Equal Area projection, so we regrid it
    """
    source_crs = source.coord_system()

    lambert_crs = iris.coord_systems.LambertConformal(
        central_lat=source_crs.latitude_of_projection_origin,
        central_lon=source_crs.longitude_of_central_meridian,
        secant_latitudes=source_crs.standard_parallels,
        false_easting=source_crs.false_easting,
        false_northing=source_crs.false_northing,
    )

    x_coord = source.coord("projection_x_coordinate").copy()
    y_coord = source.coord("projection_y_coordinate").copy()

    x_coord.coord_system = lambert_crs
    y_coord.coord_system = lambert_crs
    data = numpy.zeros((len(y_coord.points), len(x_coord.points)))

    target = iris.cube.Cube(data)
    target.add_dim_coord(y_coord, 0)
    target.add_dim_coord(x_coord, 1)
    return target


def read_rainfields3(valid: datetime, radar_id: int) -> tuple[numpy.ndarray, dict]:
    """
    Load Rainfields3 data.

    The NetCDF data is extracted from the zip files and regridded to an
    equivalent Lambert Conformal grid that MET can accept.

    The returned values should be stored in global variables 'met_data' and
    'attrs' for MET to find them.
    """
    zip_template = (
        f"/g/data/rq0/rainfields3/{radar_id}/%Y/prcp-m15/{radar_id}_%Y%m%d.prcp-m15.zip"
    )
    zip_path = valid.strftime(zip_template)

    member_template = f"{radar_id}_%Y%m%d_%H%M00.prcp-m15.nc"
    member_path = valid.strftime(member_template)

    with ZipFile(zip_path) as zf, NamedTemporaryFile(delete_on_close=False) as tf:
        buff = zf.read(member_path)
        tf.write(buff)
        tf.close()

        precip = iris.load_cube(tf.name, "precipitation")

        # Fixup units
        precip.coord("projection_x_coordinate").convert_units("m")
        precip.coord("projection_y_coordinate").convert_units("m")

        target = generate_target(precip)

        precip_regrid = precip.regrid(target, iris.analysis.Linear())

        met_data = precip_regrid.data

    crs = precip_regrid.coord_system()

    attrs = {
        "valid": valid.strftime("%Y%m%d_%H%M%S"),
        "init": valid.strftime("%Y%m%d_%H%M%S"),
        "lead": "000000",
        "accum": "001500",
        "name": "APCP_001500",
        "long_name": "precipitation",
        "level": "A001500",
        "units": "kg m-2",
        "grid": {
            "type": "Lambert Conformal",
            "name": f"RADAR_{radar_id}",
            "hemisphere": "S",
            "scale_lat_1": crs.secant_latitudes[0],
            "scale_lat_2": crs.secant_latitudes[1],
            "lat_pin": crs.central_lat,
            "lon_pin": crs.central_lon,
            "x_pin": met_data.shape[1] / 2.0,
            "y_pin": met_data.shape[0] / 2.0,
            "lon_orient": crs.central_lon,
            "d_km": 0.5,
            "r_km": 6371.2,
            "nx": met_data.shape[1],
            "ny": met_data.shape[0],
        },
    }

    return met_data, attrs


def parse_valid(t: str) -> datetime:
    """Convert a MET timestamp to a datetime."""
    return datetime.strptime(t, "%Y%m%d_%H%M")


def cli():
    """Parse the arguments from the METplus config."""
    parser = argparse.ArgumentParser()
    parser.add_argument("valid", type=parse_valid, help="Valid time")
    parser.add_argument("radar_id", type=int, help="Radar ID")
    args = parser.parse_args()

    with open(f"mask_{args.radar_id}.poly", "wt") as f:
        # We're not interested in actually masking here - just grabbing the name
        f.write(
            dedent(f"""\
            RF{args.radar_id}
            80 0
            -80 0
            -80 180
            80 180
            """)
        )
    return read_rainfields3(args.valid, args.radar_id)


# Data to pass to MET, these get read from the global variables
met_data, attrs = cli()
