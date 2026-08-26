#!/usr/bin/env python3

"""Create CSET plots from MET grid_stat output."""

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Iterable

import iris.coords
import iris.cube

from CSET.operators.plot import spatial_pcolormesh_plot

log = logging.getLogger(__name__)


def standardise_names(cube: iris.cube.Cube) -> iris.cube.Cube:
    """
    Convert the name MET gives fields to something more standard.

    From a name like
        {type}_{var0}_{levels0}(_{var1}_{levels1})?_{region}

    Sets:
        var_name to '{type}_{var0}'
        long_name to '{var0}_{long_type}'
        standard_name to '{var0}' (for OBS and FCST fields only)

    Modifies the cube in-place and returns it
    """
    assert cube.var_name is not None
    name = cube.var_name
    levels = cube.attributes["level"].split(" and ")
    mask_region = cube.attributes["masking_region"]
    type = name.split("_")[0]

    level_names = [lev.replace("*", "all").replace(",", "_") for lev in levels]

    name_middle = name[len(type) + 1 : -(len(mask_region) + 1)]

    var0 = name_middle[: name_middle.index(level_names[0]) - 1]

    cube.var_name = f"{type}_{var0}_{mask_region}"
    cube.attributes["type"] = type

    if type == "OBS":
        cube.long_name = f"{var0}_observation"
        cube.standard_name = var0
        cube.attributes["verification_type"] = "Observation Value"
    elif type == "FCST":
        cube.long_name = f"{var0}_forecast"
        cube.standard_name = var0
        cube.attributes["verification_type"] = "Forecast Value"
    elif type == "DIFF":
        cube.long_name = f"{var0}_difference"
        cube.attributes["model_var"] = var0
        cube.attributes["verification_type"] = cube.attributes["Difference"]

    return cube


def postproc_cube(cube: iris.cube.Cube, field: str, filename: str):
    """
    Prepare the MET data for processing.

    Use this as a callback when loading Iris cubes from grid_stat output.

    Fixes the names and sets up time coordinates properly
    """
    cube = standardise_names(cube)

    # Grab timestamps
    init_time_ut = int(cube.attributes.pop("init_time_ut"))
    valid_time_ut = int(cube.attributes.pop("valid_time_ut"))

    # Clean up attributes that might not match between different files
    cube.attributes.pop("init_time")
    cube.attributes.pop("valid_time")
    cube.attributes.pop("level")
    cube.attributes.pop("name")
    cube.attributes.pop("FileOrigins")

    cube.add_aux_coord(
        iris.coords.DimCoord(
            init_time_ut,
            standard_name="forecast_reference_time",
            units="seconds since 1970-01-01 00:00Z",
        )
    )
    cube.add_aux_coord(
        iris.coords.DimCoord(
            valid_time_ut, standard_name="time", units="seconds since 1970-01-01 00:00Z"
        )
    )

    if "invalid_units" in cube.attributes:
        cube.units = cube.attributes["invalid_units"].split(" and ")[0]


def load_grid_stat(paths: Iterable[Path]) -> iris.cube.CubeList:
    """Load processed grid_stat netcdf output as iris cubes."""
    cubes = iris.cube.CubeList()
    for path in paths:
        cubes.extend(iris.load(path, callback=postproc_cube))
    return cubes.merge()


def plot_grid_stat(
    cube: iris.cube.Cube,
    webdir: Path,
    *,
    style_file: Path | str | None = None,
    plot_resolution: int | None = None,
):
    """
    Create plots from grid_stat output.

    Parameters
    ----------
        cube:
            Input data cube
        webdir:
            Base web path for this cycle
        style_file:
            Colorbar definition JSON file
        plot_resolution:
            Plot resolution in pixels per inch
    """
    model = cube.attributes["model"]
    obstype = cube.attributes["obtype"]
    assert cube.var_name is not None
    outdir = webdir / "grid_stat" / f"{model}_vs_{obstype}" / cube.var_name
    outdir.mkdir(exist_ok=True, parents=True)
    os.chdir(outdir)

    log.info("writing %s to %s", cube.name(), outdir)

    # Set up CSET metadata
    meta = {
        "category": "Gridded Verification",
        "title": f"{cube.long_name}",
        "case_date": cube.coord("forecast_reference_time")
        .as_string_arrays(fmt="%Y%m%dT%H%MZ")
        .points[0],
        "MODEL_NAME": model,
        "OBSERVATION_TYPE": obstype,
        "GRID_STAT_TYPE": cube.attributes["verification_type"],
        "SUBAREA_EXTENT": cube.attributes["masking_region"],
    }

    if cube.attributes["type"] == "OBS":
        meta["title"] = f"{obstype} {cube.long_name}"
    elif cube.attributes["type"] == "FCST":
        meta["title"] = f"{model} {cube.long_name}"
    elif cube.attributes["type"] == "DIFF":
        meta["title"] = f"{model} vs {obstype} {cube.long_name}"

    with open("meta.json", "wt") as f:
        json.dump(meta, f)

    cube.coord("latitude").guess_bounds()
    cube.coord("longitude").guess_bounds()
    spatial_pcolormesh_plot(cube, f"grid_stat_DarwinCTL_vs_GPM_{cube.var_name}.png")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--web-dir", help="directory to store plots", type=Path, required=True
    )
    parser.add_argument("--style-file", help="colorbar definitions", type=Path)
    parser.add_argument("--plot-resolution", help="plot resolution", type=int)
    parser.add_argument(
        "input", help="grid_stat directories to process", type=Path, nargs="+"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    for grid_stat_dir in args.input:
        cubes = load_grid_stat(grid_stat_dir.glob("**/*.nc"))

        for cube in cubes:
            plot_grid_stat(
                cube,
                args.web_dir,
                style_file=args.style_file,
                plot_resolution=args.plot_resolution,
            )


if __name__ == "__main__":
    main()
