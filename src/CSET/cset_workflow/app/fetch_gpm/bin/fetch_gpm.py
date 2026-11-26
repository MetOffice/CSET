#! /usr/bin/env python3

"""Retrieve Global Precipitation Measurement (GPM) observations. Specific to the Met Office."""

import logging
import os
from datetime import datetime
from pathlib import Path

import iris
import isodate

from CSET.operators.read import cutout_cubes_function

logger = logging.getLogger(__name__)

iris.FUTURE.save_split_attrs = True
iris.FUTURE.date_microseconds = True

# Define the file to use when retrieving the sensitive GPM handling data.
# gpm_met_office = "restricted_gpm_met_office.json"


def _get_needed_environment_variables_gpm() -> dict:
    """Load the needed variables from the environment to retrieve GPM data."""
    variables = {
        "date_type": "initiation",
        "data_time": datetime.fromisoformat(os.environ["CYLC_TASK_CYCLE_POINT"]),
        "forecast_length": isodate.parse_duration(os.environ["ANALYSIS_LENGTH"]),
        "rose_datac": os.environ["ROSE_DATAC"],
    }
    logger.debug("Environment variables loaded for Nimrod: %s", variables)
    return variables


def _get_gpm_dict() -> dict:
    """Define the parameters required to handle GPM data in MO local archive.

    The local archive can be found at /data/users/gpm_imerg

    There are two production versions of the data in the archive,
    V06 and V07. The link current_version points to the V07 data.

    As of November 2026 the archive holds GPM V07 data
    from 1998-01-01 to 2025-09-30 inclusive.
    """
    # TODO this dictionary should be in a restricted file.
    gpm_dict = {
        "filepath": "/data/users/gpm_imerg/production/current_version",
        "filename": "gpm_imerg_production_V07B_",
        "filename_suffix": ".nc",
        "frequency": "PT24H",
        "gpm_id": "GPM",
    }
    return gpm_dict


def _get_gpm_domain_dict() -> dict:
    """Define the domains that can be used to cutout GPM data.

    The order of the latitude and longitude coordinates for each
    domain are:

    [ lower Lat, upper Lat, lower lon, upper lon ]

    This is the same format used by CSET to specify SUBAREAs.
    """
    gpm_domain_dict = {
        "ukv_domain": [48.0, 62.0, -14.0, 5.0],
    }
    return gpm_domain_dict


def retrieve_gpm():
    """Fetch the GPM observations corresponding to a model run.

    The following environment variables need to be set:
    * GPM_AREA
    * CYLC_TASK_CYCLE_POINT
    * ANALYSIS_LENGTH
    * ROSE_DATAC
    """

    # Simple function to load GPM data into an Iris cube.
    def _load_gpm(path: Path) -> iris.cube.Cube | None:
        """Load a GPM file, or return None if it's missing."""
        if not path.exists():
            logger.warning("GPM file not found: %s", path)
            return None
        return iris.load_cube(path)

    # Grab the environment variables required for handling GPM data.
    v = _get_needed_environment_variables_gpm()

    # Grab the GPM handling dictionary.
    gpm_dict = _get_gpm_dict()

    # Grab the GPM domain dictionary.
    gpm_domain_dict = _get_gpm_domain_dict()

    # Prepare the output directory for the GPM data.
    gpm_dir = Path(v["rose_datac"]) / "data" / gpm_dict["gpm_id"]
    os.makedirs(gpm_dir, exist_ok=True)
    logger.info("Cylc-run GPM directory: %s", gpm_dir)

    # Fetch GPM data between the start and end dates.
    date_use = v["data_time"]
    while date_use <= v["data_time"] + v["forecast_length"]:
        # Form the filepath to the GPM data.
        gpm_obs_path = (
            Path(gpm_dict["filepath"])
            / str(date_use.year)
            / f"{gpm_dict['filename']}{date_use:%Y%m%d}{gpm_dict['filename_suffix']}"
        )

        print("-->", gpm_obs_path)

        # Load the GPM data into an Iris cube.
        gpm_cube_obs = _load_gpm(gpm_obs_path)

        # Cut out the required GPM domain.
        subarea_type = "realworld"
        if os.environ["GPM_DOMAIN_UKV"]:
            subarea_extent = gpm_domain_dict["ukv_domain"]
            gpm_cutout_cubes = cutout_cubes_function(
                gpm_cube_obs, subarea_type, subarea_extent
            )
            gpm_cube_obs = gpm_cutout_cubes

        # TODO need a small function to fettle the GPM cubes
        # i.e. construct forecast_reference_time and forecast_period

        # Write the GPM obs to a NetCDF file.
        if gpm_cube_obs is not None:
            filename_obs_nc = (
                f"{gpm_dir}/{date_use.strftime('%Y%m%d')}_{gpm_dict['gpm_id']}"
            )
            filename_obs_nc = Path(filename_obs_nc).with_suffix(".nc")
            iris.save(gpm_cube_obs, filename_obs_nc)

        # Advance the date/time counter using the time interval
        # appropriate to the GPM data.
        date_use = date_use + isodate.parse_duration(gpm_dict["frequency"])


# Run the function that fetches the GPM obs.
if __name__ == "__main__":
    retrieve_gpm()
