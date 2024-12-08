#! /usr/bin/env python3

"""Retrieve files from the filesystem."""

from CSET._workflow_utils.fetch_data import FilesystemFileRetriever, fetch_data

fetch_data(FilesystemFileRetriever)
