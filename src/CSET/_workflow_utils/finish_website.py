#! /usr/bin/env python3

"""Write finished status to website front page.

Does the final update to the workflow status on the front page of the web
interface.
"""

import os


def run():
    """Run workflow script."""
    with open(f"{os.getenv('WEB_DIR')}/status.html", "wt") as fp:
        fp.write("<p>Finished</p>\n")
