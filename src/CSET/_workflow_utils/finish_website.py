#! /usr/bin/env python3

"""Write finished status to website front page.

Does the final update to the workflow status on the front page of the web
interface.
"""

import os


def run():
    """Run workflow script."""
    with open(os.getenv("CYLC_WORKFLOW_SHARE_DIR") + "/web/status.html", "wt") as fp:
        fp.write("<p>Finished</p>\n")
