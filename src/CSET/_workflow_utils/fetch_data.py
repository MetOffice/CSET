#! /usr/bin/env python3

"""Retrieve the files from the filesystem for the current cycle point."""

import abc
import glob
import logging
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

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
    def get_file(self, file_path: str, output_dir: str) -> None:
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
        for file in file_paths:
            try:
                shutil.copy(file, output_dir)
            except OSError as err:
                logging.warning("Failed to copy %s, error: %s", file, err)


def _template_file_path():
    """Fill time placeholders to generate a file path to fetch."""
    raw_path = os.environ["DATA_PATH"]
    date_type = os.environ["DATE_TYPE"]
    data_time = datetime.fromisoformat(os.environ["CYLC_TASK_CYCLE_POINT"])
    forecast_length = isodate.parse_duration(os.environ["CSET_ANALYSIS_PERIOD"])
    forecast_offset = isodate.parse_duration(os.environ["CSET_ANALYSIS_OFFSET"])

    placeholder_times: list[datetime] = []
    lead_times: list[timedelta] = []
    match date_type:
        case "validity":
            date = data_time
            data_period = isodate.parse_duration(os.getenv("DATA_PERIOD"))
            while date < data_time + forecast_length:
                placeholder_times.append(date)
                date += data_period
        case "initiation":
            placeholder_times.append(data_time)
        case "lead":
            placeholder_times.append(data_time)
            data_period = isodate.parse_duration(os.getenv("DATA_PERIOD"))
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
    """Fetch the model's data.

    The following environment variables need to be set:
     * CSET_ANALYSIS_OFFSET
     * CSET_ANALYSIS_PERIOD
     * CYLC_TASK_CYCLE_POINT
     * DATA_PATH
     * DATA_PERIOD - If DATE_TYPE is not 'initialisation'
     * DATE_TYPE
     * MODEL_NUMBER

    Parameters
    ----------
    file_retriever: FileRetriever
        FileRetriever implementation to use. Defaults to FilesystemFileRetriever.
    """
    # Prepare output directory.
    model_number = os.getenv("MODEL_NUMBER")
    cycle_share_data_dir = f"{os.getenv('CYLC_WORKFLOW_SHARE_DIR')}/cycle/{os.getenv('CYLC_TASK_CYCLE_POINT')}/data/{model_number}"
    os.makedirs(cycle_share_data_dir, exist_ok=True)
    logging.debug("Output directory: %s", cycle_share_data_dir)

    # Get file paths.
    paths = _template_file_path()
    logging.info("Retrieving paths:\n%s", "\n".join(paths))

    # Use file retriever to transfer data with multiple threads.
    with file_retriever() as retriever, ThreadPoolExecutor() as executor:
        for path in paths:
            executor.submit(retriever.get_file, path, cycle_share_data_dir)
