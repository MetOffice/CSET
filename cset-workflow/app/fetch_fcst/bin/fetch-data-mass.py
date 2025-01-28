#! /usr/bin/env python3

"""Retrieve files from MASS."""

import subprocess

from CSET._workflow_utils.fetch_data import FileRetrieverABC, fetch_data


class MASSFileRetriever(FileRetrieverABC):
    """Retrieve files from MASS."""

    def get_file(self, file_path: str, output_dir: str) -> None:
        """Save a file from MASS to the output directory.

        Parameters
        ----------
        file_path: str
            Path of the file to copy on MASS. It may contain patterns
            like globs, which will be expanded in a system specific manner.
        output_dir: str
            Path to filesystem directory into which the file should be copied.
        """
        subprocess.run(["moo", "get", file_path, output_dir])


fetch_data(MASSFileRetriever)
