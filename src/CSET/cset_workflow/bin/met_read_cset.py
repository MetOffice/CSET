"""
Read a CSET cube into MET.

Use in your METplus config like:

    FCST_POINT_STAT_INPUT_TEMPLATE = PYTHON_NUMPY
    FCST_POINT_STAT_VAR1_NAME = met_read_cset.py \
            --name temperature_at_screen_level \
            --valid {valid?fmt=%Y%m%dT%H%M} \
            m1.nc

Accepts one or more constraints. A constraint can be:

    --name NAME
    --valid VALID
    --name '{"standard_name": "NAME"}'
    --attr '{"method": "time: mean (1 hour)"}'
    --coord '{"time": "TIME"}'
    --constraint '{"name": [...], "attr": [...], "coord": [...]}'

`--name NAME` is converted to a Constraint(name=NAME)
`--valid VALID` is converted to a Constraint(time=VALID)

If a JSON object is provided to `--name`, `--attr` or `--coord` it is converted
to a NameConstraint, AttributeConstraint or Constraint based on the flag.

`--constraint` lets you specify multiple constraints with a single JSON object,
e.g. a user could set a custom constraint in the rose-suite.conf file.

The loaded cube is the union of all constraints. If the constraints don't
return a single cube or the cube is not a 2D slice an exception is raised.
"""

import argparse
import json
import logging
import time
from typing import Any

import iris
import numpy
import pandas

from CSET.operators.read import read_cube

log = logging.getLogger("met_read_cset")

# Output variables that MET reads
met_data: numpy.ndarray
attrs: dict[str, Any]


def met_attrs(cube: iris.cube.Cube) -> dict[str, Any]:
    """Create MET metadata from a cube."""
    attrs = {
        "valid": "NA",
        "init": "NA",
        "lead": "NA",
        "accum": "NA",
        "name": cube.name(),
        "long_name": cube.long_name,
        "level": "NA",
        "units": str(cube.units),
        "grid": {},
        "fill_value": numpy.nan,
    }

    valid = cube.coord("time").cell(0).point
    init = cube.coord("forecast_reference_time").cell(0).point
    lead = int((valid - init).total_seconds())

    attrs["valid"] = valid.strftime("%Y%m%d_%H%M%S")
    attrs["init"] = init.strftime("%Y%m%d_%H%M%S")
    attrs["lead"] = f"{lead // 60 // 60:02d}{lead // 60 % 60:02d}{lead % 60:02d}"

    try:
        attrs["fill_value"] = cube.data.fill_value
    except AttributeError:
        pass

    try:
        attrs["level"] = f"Z{cube.coord('height').points[0]}"
    except iris.exceptions.CoordinateNotFoundError:
        pass

    # For the moment only regular lat-lon grids are supported
    lats = cube.coord("latitude").points
    lons = cube.coord("longitude").points
    grid = {
        "type": "LatLon",
        "name": "CSET",
        "lat_ll": lats[0],
        "lon_ll": lons[0],
        "delta_lat": numpy.mean(numpy.diff(lats)),
        "delta_lon": numpy.mean(numpy.diff(lons)),
        "Nlat": len(lats),
        "Nlon": len(lons),
    }
    numpy.testing.assert_allclose(
        lats, grid["lat_ll"] + numpy.arange(grid["Nlat"]) * grid["delta_lat"]
    )
    numpy.testing.assert_allclose(
        lons, grid["lon_ll"] + numpy.arange(grid["Nlon"]) * grid["delta_lon"]
    )
    attrs["grid"] = grid

    log.info("MET Attributes:")
    log.info(json.dumps(attrs, indent=2, default=str))
    return attrs


def met_read_cset(
    path: str | list[str], constraint: iris.Constraint
) -> tuple[numpy.ndarray, dict[str, Any]]:
    """Read a single cube using CSET's loader into MET's format."""
    cube = read_cube(path, constraint)

    log.info("Loaded cube:")
    log.info(cube)

    if len(cube.shape) != 2:
        raise AttributeError("Loaded cube is not 2D")

    return cube.data, met_attrs(cube)


def generate_constraint(constraint: dict) -> iris.Constraint:
    """Combine the constraint dict into an iris.Constraint."""
    for k in constraint:
        if k not in ["name", "attr", "coord"]:
            raise AttributeError(f"Unknown constraint type {k}")

    cons = iris.Constraint()
    for c in constraint["name"]:
        try:
            iris.NameConstraint(*json.loads(c))
        except json.JSONDecodeError:
            cons &= iris.Constraint(name=c)
    for c in constraint["attr"]:
        cons &= iris.AttributeConstraint(**c)
    for c in constraint["coord"]:
        for k, v in c.items():
            if k == "time":
                c[k] = pandas.to_datetime(v)
        cons &= iris.Constraint(**c)

    log.debug("iris constraint:")
    log.debug(cons)

    return cons


def main() -> tuple[numpy.ndarray, dict[str, Any]]:
    """
    Handle arguments set in the METplus config file.

    Use like:

        POINT_STAT_FCST_FILE_TYPE = PYTHON_NUMPY
        FCST_POINT_STAT_INPUT_TEMPLATE = PYTHON_NUMPY
        FCST_POINT_STAT_VAR1_NAME = met_read_cset.py --valid {valid?fmt=%Y%m%dT%H%M} --name temperature_at_screen_level {INPUT_PATH}
    """
    parser = argparse.ArgumentParser(description="Read a CSET cube into MET")
    parser.add_argument("PATH", type=str, nargs="+", help="Input data paths")

    parser.add_argument(
        "--name", type=str, action="append", default=[], help="Name constraint"
    )
    parser.add_argument("--valid", type=str, help="Time constraint")
    parser.add_argument(
        "--attr",
        type=json.loads,
        action="append",
        default=[],
        help="Attribute constraint",
    )
    parser.add_argument(
        "--coord", type=json.loads, action="append", default=[], help="Coord constraint"
    )
    parser.add_argument(
        "--constraint", type=json.loads, default={}, help="General constraint"
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    # Built up the master constraint dict
    constraint = args.constraint
    for C in ["name", "attr", "coord"]:
        if C not in constraint:
            constraint[C] = getattr(args, C)
        else:
            constraint[C].extend(getattr(args, C))
    if args.valid is not None:
        constraint["coord"].append({"time": args.valid})

    log.info("Constraint:")
    log.info(json.dumps(constraint, indent=2, default=str))

    cons = generate_constraint(constraint)

    return met_read_cset(args.PATH, cons)


start = time.perf_counter()
met_data, attrs = main()
end = time.perf_counter()
log.info("met_read_cset ran in %s s", end - start)
