#! /usr/bin/env python3

"""Retrieve files via HTTP."""

import ssl
import urllib.parse
import urllib.request

from CSET._workflow_utils.fetch_data import FileRetriever, fetch_data


class HTTPFileRetriever(FileRetriever):
    """Retrieve files via HTTP."""

    def get_file(self, file_path: str, output_dir: str) -> None:
        """Save a file from a HTTP address to the output directory.

        Parameters
        ----------
        file_path: str
            Path of the file to copy on MASS. It may contain patterns
            like globs, which will be expanded in a system specific manner.
        output_dir: str
            Path to filesystem directory into which the file should be copied.
        """
        ctx = ssl.create_default_context()
        save_path = urllib.parse.urlparse(file_path).path.split("/")[-1]
        with urllib.request.urlopen(file_path, output_dir, context=ctx) as response:
            with open(save_path, "wb") as fp:
                fp.write(response.read())


fetch_data(HTTPFileRetriever)
