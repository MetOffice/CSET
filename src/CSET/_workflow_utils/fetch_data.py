#! /usr/bin/env python3

"""Retrieve the files from the filesystem for the current cycle point."""

import abc
import glob
import logging
import os
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Literal

import isodate

logging.basicConfig(
    level=os.getenv("LOGLEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s"
)


class FileRetriever(abc.ABC):
    """Abstract class for retrieving files from a data source.

    The `get_file` method must be defined. Optionally the __enter__ and __exit__
    methods maybe be overridden to add setup or cleanup code.

    The class is designed to be used as a context manager, so that resources can
    be cleaned up after the retrieval is complete. All the files of a model are
    retrieved within a single context manager block, within which the `get_file`
    method is called for each file path.
    """

    def __enter__(self) -> "FileRetriever":
        """Initialise the file retriever."""
        logging.debug("Initialising FileRetriever.")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Clean up the file retriever."""
        logging.debug("Tearing down FileRetriever.")

    @abc.abstractmethod
    def get_file(self, file_path: str, output_dir: str) -> None:  # pragma: no cover
        """Save a file from the data source to the output directory.

        Not all of the given paths will exist, so FileNotFoundErrors should be
        logged, but not raised.

        Implementations should be thread safe, as the method is called from
        multiple threads.

        Parameters
        ----------
        file_path: str
            Path of the file to copy on the data source. It may contain patterns
            like globs, which will be expanded in a system specific manner.
        output_dir: str
            Path to filesystem directory into which the file should be copied.
        """
        raise NotImplementedError


class FilesystemFileRetriever(FileRetriever):
    """Retrieve files from the filesystem."""

    def get_file(self, file_path: str, output_dir: str) -> None:
        """Save a file from the filesystem to the output directory.

        Parameters
        ----------
        file_path: str
            Path of the file to copy on the filesystem. It may contain patterns
            like globs, which will be expanded in a system specific manner.
        output_dir: str
            Path to filesystem directory into which the file should be copied.
        """
        file_paths = glob.glob(os.path.expanduser(file_path))
        logging.debug("Copying files:\n%s", "\n".join(file_paths))
        if not file_paths:
            logging.warning("file_path does not match any files: %s", file_path)
        for file in file_paths:
            try:
                shutil.copy(file, output_dir)
            except OSError as err:
                logging.warning("Failed to copy %s, error: %s", file, err)


def _get_needed_environment_variables() -> dict:
    """Load the needed variables from the environment."""
    # Python 3.10 and older don't fully support ISO 8601 datetime formats.
    # TODO: Remove once we drop python 3.10.
    if sys.version_info.minor < 11:
        _fromisoformat = isodate.parse_datetime
    else:
        _fromisoformat = datetime.fromisoformat
    variables = {
        "raw_path": os.environ["DATA_PATH"],
        "date_type": os.environ["DATE_TYPE"],
        "data_time": _fromisoformat(os.environ["CYLC_TASK_CYCLE_POINT"]),
        "forecast_length": isodate.parse_duration(os.environ["CSET_ANALYSIS_PERIOD"]),
        "forecast_offset": isodate.parse_duration(os.environ["CSET_ANALYSIS_OFFSET"]),
        "share_dir": os.environ["CYLC_WORKFLOW_SHARE_DIR"],
        "cycle_point": os.environ["CYLC_TASK_CYCLE_POINT"],
        "model_number": os.environ["MODEL_NUMBER"],
    }
    # Data period is not needed for initiation time.
    if variables["date_type"] != "initiation":
        variables["data_period"] = isodate.parse_duration(os.environ["DATA_PERIOD"])
    return variables


def _template_file_path(
    raw_path: str,
    date_type: Literal["validity", "initiation", "lead"],
    data_time: datetime,
    forecast_length: timedelta,
    forecast_offset: timedelta,
    data_period: timedelta,
) -> list[str]:
    """Fill time placeholders to generate a file path to fetch."""
    placeholder_times: list[datetime] = []
    lead_times: list[timedelta] = []
    match date_type:
        case "validity":
            date = data_time
            while date < data_time + forecast_length:
                placeholder_times.append(date)
                date += data_period
        case "initiation":
            placeholder_times.append(data_time)
        case "lead":
            placeholder_times.append(data_time)
            lead_time = forecast_offset
            while lead_time < forecast_length:
                lead_times.append(lead_time)
                lead_time += data_period
        case _:
            raise ValueError(f"Invalid date type: {date_type}")

    paths: list[str] = []
    for placeholder_time in placeholder_times:
        # Expand out all other format strings.
        path = placeholder_time.strftime(os.path.expandvars(raw_path))
        if lead_times:
            # Expand out lead time format strings, %N.
            for lead_time in lead_times:
                # BUG: Will not respect escaped % signs, e.g: %%N.
                paths.append(
                    path.replace("%N", f"{int(lead_time.total_seconds()) // 3600:03d}")
                )
        else:
            paths.append(path)
    return paths


def fetch_data(file_retriever: FileRetriever = FilesystemFileRetriever):
    """Fetch the data for a model.

    The following environment variables need to be set:
    * CSET_ANALYSIS_OFFSET
    * CSET_ANALYSIS_PERIOD
    * CYLC_TASK_CYCLE_POINT
    * CYLC_WORKFLOW_SHARE_DIR
    * DATA_PATH
    * DATA_PERIOD
    * DATE_TYPE
    * MODEL_NUMBER

    Parameters
    ----------
    file_retriever: FileRetriever
        FileRetriever implementation to use. Defaults to FilesystemFileRetriever.
    """
    v = _get_needed_environment_variables()

    # Prepare output directory.
    cycle_share_data_dir = (
        f"{v['share_dir']}/cycle/{v['cycle_point']}/data/{v['model_number']}"
    )
    os.makedirs(cycle_share_data_dir, exist_ok=True)
    logging.debug("Output directory: %s", cycle_share_data_dir)

    # Get file paths.
    paths = _template_file_path(
        v["raw_path"],
        v["date_type"],
        v["data_time"],
        v["forecast_length"],
        v["forecast_offset"],
        v["data_period"],
    )
    logging.info("Retrieving paths:\n%s", "\n".join(paths))

    # Use file retriever to transfer data with multiple threads.
    with file_retriever() as retriever, ThreadPoolExecutor() as executor:
        for path in paths:
            executor.submit(retriever.get_file, path, cycle_share_data_dir)
