#! /usr/bin/env python3

"""Convert plot records into output webpages."""

import fcntl
import gzip
import json
import os
import shutil
from pathlib import Path
from uuid import uuid4

import redis


def get_records():
    """Get records from the database as an iterator."""
    with open(
        f"{os.getenv('CYLC_WORKFLOW_SHARE_DIR')}/redis_uri", encoding="UTF-8"
    ) as fp:
        redis_uri = fp.read().strip()
    r = redis.Redis().from_url(redis_uri)
    value = r.rpop("plot_records")
    while value is not None:
        yield json.loads(value)
        value = r.rpop("plot_records")


def combine_dicts(d1: dict, d2: dict) -> dict:
    """Recursively combines two dictionaries.

    Duplicate atoms favour the second dictionary.
    """
    # TODO: Test this function, as I'm not sure it is 100% correct.
    for key in d1.keys() & d2.keys():
        if isinstance(d1[key], dict):
            d1[key] = combine_dicts(d1[key], d2[key])
        else:
            d1[key] = d2[key]
    for key in d2.keys() - d1.keys():
        d1[key] = d2[key]
    return d1


def append_to_index(index_path: Path, record: dict):
    """Append the plot record to the index file.

    Record should have the form {"Model Name": {"Plot Name": "directory-uuid"}}
    """
    with open(index_path, "a+t", encoding="UTF-8") as fp:
        # Lock file until closed.
        fcntl.flock(fp, fcntl.LOCK_EX)
        # Open in append mode then seek back to avoid errors if the file does
        # not exist.
        fp.seek(0)
        try:
            index = json.load(fp)
        except json.JSONDecodeError:
            index = {}
        index = combine_dicts(index, record)
        fp.seek(0)
        fp.truncate()
        json.dump(index, fp)


def populate_webdir(record):
    """Create a webpage for the record, and add it to the index."""
    # Make directory for plot page.
    plot_id = str(uuid4())
    webdir_path = Path(f"{os.getenv('WEB_DIR')}/plots/{plot_id}")
    webdir_path.mkdir(exist_ok=True)

    # Copy plot image.
    shutil.copyfile(record["plot_location"], webdir_path / "plot.svg")

    # Compress and write data.
    with open(record["plot_data_location"], "rb") as f_in:
        with gzip.open(webdir_path / "processed_data.nc.gz", "wb") as f_out:
            shutil.copyfileobj(f_in, f_out)

    # Copy diagnostic logs.
    shutil.copyfile(
        record["diagnostic_log_location"], webdir_path / "diagnostic-log.txt"
    )

    # Generate output webpage.
    plot_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{record["title"]}</title>
    <link rel="stylesheet" href="../../static/plot-style.css">
</head>
<body>
    <div class="diagnostic">
        <div class="plot-container">
            <img id="diagnostic-plot" src="plot.svg" alt="plot">
            <footer>
                <a id="diagnostic-plot-download" href="processed_data.nc.gz" download>
                    <button>Download plots</button>
                </a>
                <div class="horizontal-scroll">
                    <code id="diagnostic-data-path">{record["raw_data_path"]}</code>
                </div>
                <a id="diagnostic-logs" href="diagnostic-log.txt" download>
                    <button>Diagnostic logs</button>
                </a>
            </footer>
        </div>
        <aside id="description-container">
            <h2 id="diagnostic-title">{record["title"]}</h2>
            <div id="diagnostic-description">{record["description"]}</div>
        </aside>
    </div>
</body>"""
    with open(webdir_path / "index.html", "wt", encoding="UTF-8") as fp:
        fp.write(plot_html)

    # Write to index files further up.
    # Diagnostics index
    append_to_index(
        webdir_path.parent / "index.json", {record["model"]: {record["title"]: plot_id}}
    )


if __name__ == "__main__":
    for record in get_records():
        populate_webdir(record)
