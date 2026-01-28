#! /usr/bin/env python3

"""Retrieve UK radar observations. Specific to the Met Office."""

import logging
import os
import shutil
from datetime import datetime, timedelta

import isodate

# import cube_utils
# import time

# import dateutil
# import iris
# import iris.coords
# import iris.cube

# import agg_regrid
# import numpy as np
# from iris.experimental.regrid_conservative import regrid_conservative_via_esmpy

# from ants.regrid.rectilinear import TwoStage
# from CSET._workflow_utils.fetch_data import FileRetrieverABC, fetch_nimrod

# from CSET.cset_workflow.app.fetch_fcst.bin.fetch_data import (
#    FileRetrieverABC,
#    fetch_nimrod,
# )


def _get_needed_environment_variables_nimrod() -> dict:
    """Load the needed variables from the environment to retrieve UK Nimrod data."""
    variables = {
        "field": [
            os.environ["NIMROD_FIELDS_COMP_HOUR"],
            os.environ["NIMROD_FIELDS_1KM"],
            os.environ["NIMROD_FIELDS_2KM"],
        ],
        "raw_path": "/data/users/radar/UKnimrod",
        "date_type": "initiation",
        "data_time": datetime.fromisoformat(os.environ["CYLC_TASK_CYCLE_POINT"]),
        "forecast_length": isodate.parse_duration(os.environ["ANALYSIS_LENGTH"]),
        "model_identifier": "Nimrod",
        "rose_datac": os.environ["ROSE_DATAC"],
    }
    logging.debug("Environment variables loaded for Nimrod: %s", variables)
    return variables


def _template_nimrod_files(field, use_date) -> dict:
    """Write the dictionary to retrieve Nimrod obs."""
    files = {
        "rainaccum_comp_hour": {
            "basedir": "/data/users/radar/UKnimrod",
            "dir": "rainaccum_comp_hour",
            "fname": "_nimrod_ng_radar_rainaccum_comp_hour",
            "weights_dir": "rainaccwt_comp_hour",
            "weights_fname": "_nimrod_ng_radar_rainaccwt_comp_hour",
            "freq": "1hour",
        },
        "rainaccum_comp_hour_1km_cutout": {
            "basedir": "/data/users/radar/UKnimrod",
            "dir": "rainaccum_comp_hour_1km_cutout",
            "fname": "_nimrod_ng_radar_rainaccum_comp_hour_1km_cutout_775X640_eng",
            "weights_dir": "rainaccwt_comp_hour_1km_cutout",
            "weights_fname": "_nimrod_ng_radar_rainaccwt_comp_hour_1km_cutout_775X640_eng",
            "freq": "1hour",
        },
        "rainaccum_comp_hour_2km": {
            "basedir": "/data/users/radar/UKnimrod",
            "dir": "rainaccum_comp_hour_2km",
            "fname": "_nimrod_ng_radar_rainaccum_comp_hour_2km",
            "weights_dir": "rainaccwt_comp_hour_2km",
            "weights_fname": "_nimrod_ng_radar_rainaccwt_comp_hour_2km",
            "freq": "1hour",
        },
    }

    # initialise the dictionary to return, putting in null values of "None"
    filepath = {"obs": "None", "weights": "None"}

    if field in files.keys():
        # form the filename of the Nimrod obs file to retrieve from the RMED archive
        nextfile = (
            files[field]["basedir"]
            + "/"
            + files[field]["dir"]
            + "/"
            + f"{use_date.year}/{use_date.strftime('%Y%m%d%H')}00"
            + files[field]["fname"]
        )
        filepath["obs"] = nextfile

        # form the filename of the corresponding Nimrod obs weighting file to retrieve
        nextfile = (
            files[field]["basedir"]
            + "/"
            + files[field]["weights_dir"]
            + "/"
            + f"{use_date.year}/{use_date.strftime('%Y%m%d%H')}00"
            + files[field]["weights_fname"]
        )
        filepath["weights"] = nextfile

    return filepath


def _get_nimrod_file_paths(start_date, end_date, fields):
    filepaths: set[str] = set()
    use_date = start_date
    while use_date <= end_date:
        for next_field in fields:
            # form the Nimrod file names
            files = _template_nimrod_files(next_field, use_date)
            if files["obs"] != "None":
                filepaths.add(files["obs"])
                filepaths.add(files["weights"])

        # advance the date/time counter on a hour
        use_date = use_date + timedelta(hours=1)

    return filepaths


# def fetch_nimrod(nimrod_retriever: FileRetrieverABC):
def fetch_nimrod():
    # def fetch_nimrod(file_retriever: FileRetrieverABC):
    """Fetch the observations corresponding to a model run.

    The following environment variables need to be set:
    * NIMROD_FIELDs
    #* ANALYSIS_OFFSET
    #* ANALYSIS_LENGTH
    #* CYLC_TASK_CYCLE_POINT
    * DATA_PATH
    #* DATA_PERIOD
    #* DATE_TYPE
    #* MODEL_IDENTIFIER
    * ROSE_DATAC

    Parameters
    ----------
    nimrod_retriever: ObsRetriever
    ObsRetriever implementation to use. Defaults to FilesystemFileRetriever.

    Raises
    ------
    FileNotFound:
        If no observations are available.
    """
    v = _get_needed_environment_variables_nimrod()

    # Prepare output directory.
    cycle_nimrod_dir = f"{v['rose_datac']}/data/Nimrod"
    os.makedirs(cycle_nimrod_dir, exist_ok=True)
    logging.debug("Nimrod directory: %s", cycle_nimrod_dir)

    # form the Nimrod files to use
    start_date = v["data_time"]
    end_date = v["data_time"] + v["forecast_length"]
    filepaths: set[str] = set()
    filepaths = _get_nimrod_file_paths(start_date, end_date, v["field"])

    # copy the Nimrod files from the archive to the local directory
    print(" Copying Nimrod files to directory: ", cycle_nimrod_dir)
    for i in filepaths:
        print(" Grabbing Nimrod file: ", i)
        shutil.copy(i, cycle_nimrod_dir)

    return


# fetch_nimrod(NimrodRetriever())


# Run the function that fetches the NImrod radar obs.
fetch_nimrod()
