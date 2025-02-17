#! /usr/bin/env python3

"""Retrieve files from MASS."""

import logging
import subprocess
import sys

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

        Returns
        -------
        bool:
            True if files were transferred, otherwise False.
        """
        moo_command = ["moo", "get", file_path, output_dir]
        logging.debug(f"Fetching from MASS with:\n{' '.join(moo_command)}")
        p = subprocess.run(moo_command)
        if p.returncode > 0:
            logging.info(
                "moo get exited with non-zero code %s.\nstdout: %s\nstderr: %s",
                p.returncode,
                p.stdout.decode(sys.stdout.encoding),
                p.stderr.decode(sys.stderr.encoding),
            )
            return False
        return True


fetch_data(MASSFileRetriever)
