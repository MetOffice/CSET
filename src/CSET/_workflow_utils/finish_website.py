#! /usr/bin/env python3

"""Write finished status to website front page.

Constructs the plot index, and does the final update to the workflow status on
the front page of the web interface.
"""

import json
import logging
import os
from pathlib import Path

from CSET._common import combine_dicts

logging.basicConfig(
    level=os.getenv("LOGLEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s"
)


def construct_index():
    """Construct the plot index.

    Index should has the form ``{"Category Name": {"recipe_id": "Plot Name"}}``
    where ``recipe_id`` is the name of the plot's directory.
    """
    index = {}
    plots_dir = Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"] + "/web/plots")
    # Loop over all directories, and append to index.
    # Only visits the directories directly under the plots directory.
    for directory in (d for d in plots_dir.iterdir() if d.is_dir()):
        try:
            with open(directory / "meta.json", "rt", encoding="UTF-8") as fp:
                plot_metadata = json.load(fp)
            record = {
                plot_metadata["category"]: {
                    directory.name: f"{plot_metadata['title']} {os.getenv('CYLC_TASK_CYCLE_POINT', '')}".strip()
                }
            }
        except FileNotFoundError:
            # Skip directories without metadata, as are likely not plots.
            logging.debug("No meta.json in %s, skipping.", directory)
            continue
        except (json.JSONDecodeError, KeyError, TypeError) as err:
            logging.error("%s is invalid, skipping.\n%s", directory / "meta.json", err)
            continue
        index = combine_dicts(index, record)

    with open(plots_dir / "index.json", "wt", encoding="UTF-8") as fp:
        json.dump(index, fp, indent=2)


def update_workflow_status():
    """Update the workflow status on the front page of the web interface."""
    web_dir = Path(os.environ["CYLC_WORKFLOW_SHARE_DIR"] + "/web")
    with open(web_dir / "status.html", "wt") as fp:
        fp.write("<p>Finished</p>\n")


def run():
    """Do the final steps to finish the website."""
    construct_index()
    update_workflow_status()
