#! /usr/bin/env python3

"""Retrieve UK Nimrod radar observations. Specific to the Met Office."""

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path

import iris
import isodate
import numpy as np

logger = logging.getLogger(__name__)

iris.FUTURE.save_split_attrs = True
iris.FUTURE.date_microseconds = True

# Define the file to use when retrieving the sensitive Nimrod handling data.
nimrod_met_office = "restricted_nimrod_met_office.json"


def _get_needed_environment_variables_nimrod() -> dict:
    """Load the needed variables from the environment to retrieve UK Nimrod data."""
    radar_sources = []
    if os.environ["NIMROD_COMP_XKM"] == "True":
        radar_sources.append("Nimrod_comp_xkm")
    if os.environ["NIMROD_COMP_1KM"] == "True":
        radar_sources.append("Nimrod_comp_1km")
    if os.environ["NIMROD_COMP_2KM"] == "True":
        radar_sources.append("Nimrod_comp_2km")
    if os.environ["NIMROD_COMP_5MIN"] == "True":
        radar_sources.append("Nimrod_comp_5min")
    variables = {
        "field": radar_sources,
        "weights": os.environ["NIMROD_WEIGHTS"],
        "date_type": "initiation",
        "data_time": datetime.fromisoformat(os.environ["CYLC_TASK_CYCLE_POINT"]),
        "forecast_length": isodate.parse_duration(os.environ["ANALYSIS_LENGTH"]),
        "rose_datac": os.environ["ROSE_DATAC"],
    }
    logger.debug("Environment variables loaded for Nimrod: %s", variables)
    return variables


def apply_radar_weights(cube_obs: iris.cube.Cube, cube_wei: iris.cube.Cube):
    """Apply the Nimrod weights to the radar hourly rainfall accumulation data.

    Parameters
    ----------
    cube_obs: Cube or
        2 dimensional Cube of the radar rainfall accumulation data.

    cube_wei: Cube or
        2 dimensional Cube of the Nimrod rainfall accumulation weights.

    """
    # The weights are the number of 5 minute rainfall rates used to
    # compute the hourly rainfall accumulation. The weight should be
    # in the range 0 to 13.
    # Define the minimum weight to accept as good data.
    weight_min = 11

    # Define the value to use for duff radar data
    duff_value = 0.0

    # Check if the weights are packed as weights / 32
    # and if they are, unpack them.
    # Note: if the weights are packed, then the maximum value
    #       found will be 13 / 32 = 0.40625, i.e. all values < 1.
    weights = cube_wei.data
    if weights.max() < 1.0:
        weights = (weights * 32).round().astype(int)
        cube_wei.data = weights
        logger.info("Unpacked Nimrod weights file.")

    # Apply the weights.
    cube_obs_weighted = cube_obs
    cube_obs_weighted.data = np.where(
        weights < weight_min, duff_value, cube_obs_weighted.data
    )

    # Return the QC'd Nimrod data and the weights used.
    return cube_obs_weighted, cube_wei


def retrieve_nimrod():
    """Fetch the observations corresponding to a model run.

    The following environment variables need to be set:
    * NIMROD_COMP_XKM, NIMROD_COMP_1KM, NIMROD_COMP_2KM, NIMROD_COMP_5MIN
    * CYLC_TASK_CYCLE_POINT
    * ANALYSIS_LENGTH
    * ROSE_DATAC
    """

    # Grab the environment variables required for handling Nimrod data.
    def _load_nimrod(path: Path) -> iris.cube.Cube | None:
        """Load a Nimrod file, or return None if it's missing."""
        if not path.exists():
            logger.warning("Nimrod file not found: %s", path)
            return None
        return iris.load_cube(path)

    v = _get_needed_environment_variables_nimrod()

    # Grab the Nimrod handling dictionary.
    with open(nimrod_met_office, "rt") as fp:  # pragma: no cover
        nimrod_dict = json.load(fp)

    # Loop over the required Nimrod fields, i.e. 1km 2km or xkm rainfall
    # accumulation composites or the 5 minute rainfall rate composites.
    for nimrod_field in v["field"]:
        if nimrod_field:
            logger.info("Processing Nimrod field: %s", nimrod_field)
            nimrod_cfg = nimrod_dict[nimrod_field]
            # Prepare the output directory for the Nimrod field.
            nimrod_dir = Path(v["rose_datac"]) / "data" / nimrod_cfg["obs_id"]
            os.makedirs(nimrod_dir, exist_ok=True)
            logger.info("Cylc-run Nimrod directory: %s", nimrod_dir)

            # Prepare the output directory for the Nimrod weights field.
            if nimrod_dict[nimrod_field]["weights_fname"]:
                nimrod_dir_wei = Path(v["rose_datac"]) / "data" / nimrod_cfg["wei_id"]
                os.makedirs(nimrod_dir_wei, exist_ok=True)
                logger.info("Cylc-run Nimrod weights directory: %s", nimrod_dir_wei)

            # Put +1 hour offset for accumulation radar files as
            # the time stamps for these files mark the end of the
            # accumulation period rather than the beginning.
            radar_offset = timedelta(hours=0.0)
            if nimrod_field == "Nimrod_comp_xkm":
                radar_offset = timedelta(hours=1.0)
            if nimrod_field == "Nimrod_comp_1km":
                radar_offset = timedelta(hours=1.0)
            if nimrod_field == "Nimrod_comp_2km":
                radar_offset = timedelta(hours=1.0)
            date_start_offset = v["data_time"] + radar_offset

            # Process Nimrod data between the start and end dates.
            date_use = date_start_offset
            while date_use < date_start_offset + v["forecast_length"]:
                # Load the Nimrod data into an Iris cube.

                nimrod_obs_path = (
                    Path(nimrod_cfg["basedir"])
                    / nimrod_cfg["obs_dir"]
                    / str(date_use.year)
                    / f"{date_use:%Y%m%d%H%M}{nimrod_cfg['obs_fname']}"
                )

                nimrod_cube_obs = _load_nimrod(nimrod_obs_path)

                # Load the Nimrod weights into an Iris cube.
                nimrod_cube_weights = None
                if nimrod_cfg["weights_fname"]:
                    nimrod_weights_path = (
                        Path(nimrod_cfg["basedir"])
                        / nimrod_cfg["weights_dir"]
                        / str(date_use.year)
                        / f"{date_use:%Y%m%d%H%M}{nimrod_cfg['weights_fname']}"
                    )

                    nimrod_cube_weights = _load_nimrod(nimrod_weights_path)

                    if nimrod_cube_weights is not None:
                        # Ensure that the weights are unitless.
                        nimrod_cube_weights.units = "1"

                # QC the the Nimrod observations using the weights field.
                if nimrod_cube_obs is not None and nimrod_cube_weights is not None:
                    nimrod_cube_obs, nimrod_cube_weights = apply_radar_weights(
                        nimrod_cube_obs, nimrod_cube_weights
                    )

                # Now that the accumulation weights have been applied if required,
                # write the Nimrod obs to a NetCDF file.
                if nimrod_cube_obs is not None:
                    filename_obs_nc = (
                        f"{nimrod_dir}/{date_use.strftime('%Y%m%d%H%M')}"
                        f"_{nimrod_dict[nimrod_field]['obs_id']}"
                    )
                    filename_obs_nc = Path(filename_obs_nc).with_suffix(".nc")
                    iris.save(nimrod_cube_obs, filename_obs_nc)

                # Write the Nimrod weights to a NetCDF file if the switch
                # for this is set in v["weights"].
                if v["weights"] == "True" and nimrod_cube_weights is not None:
                    filename_wei_nc = (
                        f"{nimrod_dir_wei}/{date_use.strftime('%Y%m%d%H%M')}"
                        f"_{nimrod_dict[nimrod_field]['obs_id']}_weights"
                    )
                    filename_wei_nc = Path(filename_wei_nc).with_suffix(".nc")
                    iris.save(nimrod_cube_weights, filename_wei_nc)

                # Advance the date/time counter using the time interval
                # appropriate to the Nimrod field.
                date_use = date_use + isodate.parse_duration(
                    nimrod_dict[nimrod_field]["freq"]
                )


# Run the function that fetches the Nimrod radar obs.
if __name__ == "__main__":
    retrieve_nimrod()
