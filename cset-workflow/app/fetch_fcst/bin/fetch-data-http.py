#! /usr/bin/env python3

"""Retrieve files via HTTP."""

from CSET._workflow_utils.fetch_data import HTTPFileRetriever, fetch_data

fetch_data(HTTPFileRetriever)
