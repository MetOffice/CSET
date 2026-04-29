#! /usr/bin/env python3

"""Retrieve UK Nimrod radar observations. Specific to the Met Office."""

import logging
import os
from datetime import datetime
from pathlib import Path

import iris
import isodate
import numpy as np

iris.FUTURE.save_split_attrs = True
iris.FUTURE.date_microseconds = True


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
        "raw_path": "/data/users/radar/UKnimrod",
        "date_type": "initiation",
        "data_time": datetime.fromisoformat(os.environ["CYLC_TASK_CYCLE_POINT"]),
        "forecast_length": isodate.parse_duration(os.environ["ANALYSIS_LENGTH"]),
        "rose_datac": os.environ["ROSE_DATAC"],
    }
    logging.debug("Environment variables loaded for Nimrod: %s", variables)
    return variables


def _nimrod_dictionary() -> dict:
    """Write the dictionary to handle Nimrod obs."""
    nimrod_dict = {
        "Nimrod_comp_xkm": {
            "basedir": "/data/users/radar/UKnimrod",
            "obs_dir": "rainaccum_comp_hour",
            "obs_fname": "_nimrod_ng_radar_rainaccum_comp_hour",
            "weights_dir": "rainaccwt_comp_hour",
            "weights_fname": "_nimrod_ng_radar_rainaccwt_comp_hour",
            "obs_id": "Nimrodxkm",
            "wei_id": "Nimrodxkm_weights",
            "freq": "PT1H",
        },
        "Nimrod_comp_1km": {
            "basedir": "/data/users/radar/UKnimrod",
            "obs_dir": "rainaccum_comp_hour_1km_cutout",
            "obs_fname": "_nimrod_ng_radar_rainaccum_comp_hour_1km_cutout_775X640_eng",
            "weights_dir": "rainaccwt_comp_hour_1km_cutout",
            "weights_fname": "_nimrod_ng_radar_rainaccwt_comp_hour_1km_cutout_775X640_eng",
            "obs_id": "Nimrod1km",
            "wei_id": "Nimrod1km_weights",
            "freq": "PT1H",
        },
        "Nimrod_comp_2km": {
            "basedir": "/data/users/radar/UKnimrod",
            "obs_dir": "rainaccum_comp_hour_2km",
            "obs_fname": "_nimrod_ng_radar_rainaccum_comp_hour_2km",
            "weights_dir": "rainaccwt_comp_hour_2km",
            "weights_fname": "_nimrod_ng_radar_rainaccwt_comp_hour_2km",
            "obs_id": "Nimrod2km",
            "wei_id": "Nimrod2km_weights",
            "freq": "PT1H",
        },
        "Nimrod_comp_5min": {
            "basedir": "/data/users/radar/UKnimrod",
            "obs_dir": "rainrate_comp_5min",
            "obs_fname": "_nimrod_ng_radar_rainrate_composite_1km_merged",
            "weights_dir": "",
            "weights_fname": "",
            "obs_id": "Nimrod5min",
            "wei_id": "",
            "freq": "PT5M",
        },
    }

    return nimrod_dict


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
        logging.debug("Unpacked Nimrod weights file.")

    # Apply the weights.
    cube_obs_weighted = cube_obs
    cube_obs_weighted.data = np.where(
        weights < weight_min, duff_value, cube_obs_weighted.data
    )

    # Return the QC'd Nimrod data.
    return cube_obs_weighted


def retrieve_nimrod():
    """Fetch the observations corresponding to a model run.

    The following environment variables need to be set:
    * NIMROD_COMP_XKM, NIMROD_COMP_1KM, NIMROD_COMP_2KM, NIMROD_COMP_5MIN
    * CYLC_TASK_CYCLE_POINT
    * ANALYSIS_LENGTH
    * ROSE_DATAC

    Raises
    ------
    FileNotFound:
        If no observations are available.
    """
    # Grab the environment variables required for handling Nimrod data.
    v = _get_needed_environment_variables_nimrod()

    # Grab the Nimrod handling dictionary.
    nimrod_dict = _nimrod_dictionary()

    # Form the Nimrod start and end dates.
    date_start = v["data_time"]
    date_end = v["data_time"] + v["forecast_length"]

    # Loop over the required Nimrod fields, i.e. 1km 2km or xkm rainfall
    # accumulation composites or the 5 minute rainfall rate composites.
    for nimrod_field in v["field"]:
        if nimrod_field:
            logging.debug("Processing Nimrod field: %s", nimrod_field)

            # Prepare the output directory for the Nimrod field.
            nimrod_dir = f"{v['rose_datac']}/data/{nimrod_dict[nimrod_field]['obs_id']}"
            os.makedirs(nimrod_dir, exist_ok=True)
            logging.debug("Nimrod directory: %s", nimrod_dir)

            # Process Nimrod data between the start and end dates.
            date_use = date_start
            while date_use <= date_end:
                # Advance the date/time counter using the time interval appropriate to the Nimrod field.
                date_use = date_use + isodate.parse_duration(
                    nimrod_dict[nimrod_field]["freq"]
                )

                # Form the file name for the Nimrod field in the archive.
                nimrod_obs = (
                    f"{nimrod_dict[nimrod_field]['basedir']}/"
                    f"{nimrod_dict[nimrod_field]['obs_dir']}/"
                    f"{date_use.year}/{date_use.strftime('%Y%m%d%H%M')}"
                    f"{nimrod_dict[nimrod_field]['obs_fname']}"
                )

                # Load the Nimrod data into an Iris cube.
                # TODO: check that the Nimrod file exists, and handle the situation
                #       if it doesn't
                nimrod_cube_obs = iris.load_cube(nimrod_obs)

                # Form the file name for the Nimrod field weighting file in the archive,
                # read the weighting file into an Iris cube, apply the weightings to
                # the Nimrod rain field then save the weighting data as a NetCDF.
                if nimrod_dict[nimrod_field]["weights_fname"]:
                    # Prepare the output directory for the Nimrod weights data.
                    nimrod_dir_wei = (
                        f"{v['rose_datac']}/data/{nimrod_dict[nimrod_field]['wei_id']}"
                    )
                    os.makedirs(nimrod_dir_wei, exist_ok=True)
                    logging.debug("Nimrod weights directory: %s", nimrod_dir_wei)

                    nimrod_weights = (
                        f"{nimrod_dict[nimrod_field]['basedir']}/"
                        f"{nimrod_dict[nimrod_field]['weights_dir']}/"
                        f"{date_use.year}/{date_use.strftime('%Y%m%d%H%M')}"
                        f"{nimrod_dict[nimrod_field]['weights_fname']}"
                    )

                    # Load the Nimrod weights into an Iris cube.
                    # TODO: check that the Nimrod weights file exists, and handle the situation
                    #       if it doesn't
                    nimrod_cube_weights = iris.load_cube(nimrod_weights)

                    # Apply the weights to the Nimrod obs.
                    nimrod_cube_obs = apply_radar_weights(
                        nimrod_cube_obs, nimrod_cube_weights
                    )

                    # Write the Nimrod weights to a NetCDF file.
                    filename_wei_nc = (
                        f"{nimrod_dir_wei}/{date_use.strftime('%Y%m%d%H%M')}"
                        f"_{nimrod_dict[nimrod_field]['obs_id']}_weights"
                    )
                    filename_wei_nc = Path(filename_wei_nc).with_suffix(".nc")
                    iris.save(nimrod_cube_weights, filename_wei_nc)

                # Write the Nimrod obs to a NetCDF file.
                filename_obs_nc = (
                    f"{nimrod_dir}/{date_use.strftime('%Y%m%d%H%M')}"
                    f"_{nimrod_dict[nimrod_field]['obs_id']}"
                )
                filename_obs_nc = Path(filename_obs_nc).with_suffix(".nc")
                iris.save(nimrod_cube_obs, filename_obs_nc)


# Run the function that fetches the NImrod radar obs.
retrieve_nimrod()
