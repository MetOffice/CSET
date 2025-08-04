# © Crown copyright, Met Office (2022-2025) and CSET contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Retrieve the files from the filesystem for the current cycle point."""

import abc
import ast
import glob
import itertools
import logging
import os
import ssl
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal

import isodate

logging.basicConfig(
    level=os.getenv("LOGLEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s"
)


class FileRetrieverABC(abc.ABC):
    """Abstract base class for retrieving files from a data source.

    The `get_file` method must be defined. Optionally the __enter__ and __exit__
    methods maybe be overridden to add setup or cleanup code.

    The class is designed to be used as a context manager, so that resources can
    be cleaned up after the retrieval is complete. All the files of a model are
    retrieved within a single context manager block, within which the `get_file`
    method is called for each file path.
    """

    def __enter__(self) -> "FileRetrieverABC":
        """Initialise the file retriever."""
        logging.debug("Initialising FileRetriever.")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Clean up the file retriever."""
        logging.debug("Tearing down FileRetriever.")

    @abc.abstractmethod
    def get_file(self, file_path: str, output_dir: str) -> bool:  # pragma: no cover
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

        Returns
        -------
        bool:
            True if files were transferred, otherwise False.
        """
        raise NotImplementedError


class FilesystemFileRetriever(FileRetrieverABC):
    """Retrieve files from the filesystem."""

    def get_file(self, file_path: str, output_dir: str) -> bool:
        """Save a file from the filesystem to the output directory.

        Parameters
        ----------
        file_path: str
            Path of the file to copy on the filesystem. It may contain patterns
            like globs, which will be expanded in a system specific manner.
        output_dir: str
            Path to filesystem directory into which the file should be copied.

        Returns
        -------
        bool:
            True if files were transferred, otherwise False.
        """
        file_paths = glob.glob(os.path.expanduser(file_path))
        logging.debug("Copying files:\n%s", "\n".join(file_paths))
        if not file_paths:
            logging.warning("file_path does not match any files: %s", file_path)
        any_files_copied = False
        for f in file_paths:
            file = Path(f)
            try:
                # We know file exists from glob.
                os.symlink(file.absolute(), f"{output_dir}/{file.name}")
                any_files_copied = True
            except OSError as err:
                logging.warning("Failed to copy %s, error: %s", file, err)
        return any_files_copied


class HTTPFileRetriever(FileRetrieverABC):
    """Retrieve files via HTTP."""

    def get_file(self, file_path: str, output_dir: str) -> bool:
        """Save a file from a HTTP address to the output directory.

        Parameters
        ----------
        file_path: str
            Path of the file to copy on MASS. It may contain patterns like
            globs, which will be expanded in a system specific manner.
        output_dir: str
            Path to filesystem directory into which the file should be copied.

        Returns
        -------
        bool:
            True if files were transferred, otherwise False.
        """
        ctx = ssl.create_default_context()
        # Needed to enable compatibility with malformed iBoss TLS certificates.
        ctx.verify_flags &= ~ssl.VERIFY_X509_STRICT
        save_path = (
            f"{output_dir.removesuffix('/')}/"
            + urllib.parse.urlparse(file_path).path.split("/")[-1]
        )
        any_files_copied = False
        try:
            with urllib.request.urlopen(file_path, timeout=30, context=ctx) as response:
                with open(save_path, "wb") as fp:
                    # Read in 1 MiB chunks so data needn't fit in memory.
                    while data := response.read(1024 * 1024):
                        fp.write(data)
                any_files_copied = True
        except OSError as err:
            logging.warning("Failed to retrieve %s, error: %s", file_path, err)
        return any_files_copied


def _get_needed_environment_variables() -> dict:
    """Load the needed variables from the environment."""
    variables = {
        "raw_path": os.environ["DATA_PATH"],
        "date_type": os.environ["DATE_TYPE"],
        "data_time": datetime.fromisoformat(os.environ["CYLC_TASK_CYCLE_POINT"]),
        "forecast_length": isodate.parse_duration(os.environ["ANALYSIS_LENGTH"]),
        "forecast_offset": isodate.parse_duration(os.environ["ANALYSIS_OFFSET"]),
        "model_identifier": os.environ["MODEL_IDENTIFIER"],
        "rose_datac": os.environ["ROSE_DATAC"],
    }
    try:
        variables["data_period"] = isodate.parse_duration(os.environ["DATA_PERIOD"])
    except KeyError:
        # Data period is not needed for initiation time.
        if variables["date_type"] != "initiation":
            raise
        variables["data_period"] = None
    logging.debug("Environment variables loaded: %s", variables)
    return variables


def _get_needed_environment_variables_obs() -> dict:
    """Load the needed variables from the environment."""
    variables = {
        "subtype": os.environ["OBS_SUBTYPE"],
        "data_time": datetime.fromisoformat(os.environ["CYLC_TASK_CYCLE_POINT"]),
        "forecast_length": isodate.parse_duration(os.environ["ANALYSIS_LENGTH"]),
        "obs_fields": ast.literal_eval(os.environ["SURFACE_SYNOP_FIELDS"]),
        "model_identifier": "OBS",
        "wmo_nmbrs": ast.literal_eval(os.environ.get("WMO_BLOCK_STTN_NMBRS"))
        if len(os.environ.get("WMO_BLOCK_STTN_NMBRS")) > 0
        else None,
        "subarea_extent": ast.literal_eval(os.environ.get("SUBAREA_EXTENT"))
        if len(os.environ.get("SUBAREA_EXTENT")) > 0
        else None,
        "obs_interval": isodate.parse_duration(os.environ["SURFACE_SYNOP_INTERVAL"]),
        "obs_offset": isodate.parse_duration(os.environ["SURFACE_SYNOP_OFFSET"]),
        "rose_datac": os.environ["ROSE_DATAC"],
    }
    logging.debug("Environment variables loaded: %s", variables)
    return variables


def _template_file_path(
    raw_path: str,
    date_type: Literal["validity", "initiation"],
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
            lead_time = forecast_offset
            while lead_time < forecast_length:
                lead_times.append(lead_time)
                lead_time += data_period
        case _:
            raise ValueError(f"Invalid date type: {date_type}")

    paths: set[str] = set()
    for placeholder_time in placeholder_times:
        # Expand out all other format strings.
        path = placeholder_time.strftime(os.path.expandvars(raw_path))
        if lead_times:
            # Expand out lead time format strings, %N.
            for lead_time in lead_times:
                # BUG: Will not respect escaped % signs, e.g: %%N.
                paths.add(
                    path.replace("%N", f"{int(lead_time.total_seconds()) // 3600:03d}")
                )
        else:
            paths.add(path)
    return sorted(paths)


def fetch_data(file_retriever: FileRetrieverABC):
    """Fetch the data for a model.

    The following environment variables need to be set:
    * ANALYSIS_OFFSET
    * ANALYSIS_LENGTH
    * CYLC_TASK_CYCLE_POINT
    * DATA_PATH
    * DATA_PERIOD
    * DATE_TYPE
    * MODEL_IDENTIFIER
    * ROSE_DATAC

    Parameters
    ----------
    file_retriever: FileRetriever
        FileRetriever implementation to use.

    Raises
    ------
    FileNotFound:
        If no files are found for the model, across all tried paths.
    """
    v = _get_needed_environment_variables()

    # Prepare output directory.
    cycle_data_dir = f"{v['rose_datac']}/data/{v['model_identifier']}"
    os.makedirs(cycle_data_dir, exist_ok=True)
    logging.debug("Output directory: %s", cycle_data_dir)

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
        files_found = any(
            executor.map(retriever.get_file, paths, itertools.repeat(cycle_data_dir))
        )
    # We don't need to exhaust the iterator, as all futures are submitted
    # before map yields anything. Therefore they will all be resolved upon
    # exiting the with block.
    if not files_found:
        raise FileNotFoundError("No files found for model!")


def fetch_obs(obs_retriever: FileRetrieverABC):
    """Fetch the observations corresponding to a model run.

    The following environment variables need to be set:
    * ANALYSIS_OFFSET
    * ANALYSIS_LENGTH
    * CYLC_TASK_CYCLE_POINT
    * DATA_PATH
    * DATA_PERIOD
    * DATE_TYPE
    * MODEL_IDENTIFIER
    * ROSE_DATAC

    Parameters
    ----------
    obs_retriever: ObsRetriever
        ObsRetriever implementation to use. Defaults to FilesystemFileRetriever.

    Raises
    ------
    FileNotFound:
        If no observations are available.
    """
    v = _get_needed_environment_variables_obs()

    # Prepare output directory.
    cycle_obs_dir = f"{v['rose_datac']}/data/OBS"
    os.makedirs(cycle_obs_dir, exist_ok=True)
    logging.debug("Output directory: %s", cycle_obs_dir)

    # We will get just one file for now, but follow the templating
    # syntax for the model for consistency.
    obs_base_path = (
        v["subtype"]
        + "_"
        + "%Y%m%dT%H%MZ_dt_"
        + str(int(v["forecast_length"].total_seconds() // 3600)).zfill(3)
        + ".nc"
    )
    paths = _template_file_path(
        obs_base_path,
        "initiation",
        v["data_time"],
        v["forecast_length"],
        timedelta(seconds=0),
        v["obs_interval"],
    )
    logging.info("Retrieving paths:\n%s", "\n".join(paths))

    # Use obs retriever to transfer data with multiple threads.
    # We shouldn't need to iterate as we do for the forecast data
    # because these files will be smaller.
    try:
        obs_retriever.get_file(
            paths[0],
            v["subtype"],
            v["obs_fields"],
            v["data_time"],
            v["obs_offset"],
            v["forecast_length"],
            v["obs_interval"],
            cycle_obs_dir,
            wmo_nmbrs=v["wmo_nmbrs"],
            subarea_extent=v["subarea_extent"],
        )
    except Exception as exc:
        raise ValueError("No observations available.") from exc
