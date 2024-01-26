#! /usr/bin/env python3

"""Write finished status to website front page.

Does the final update to the workflow status on the front page of the web
interface.
"""

import os

with open(f"{os.getenv('WEB_DIR')}/status.json", "wt") as fp:
    fp.write("<p>Finished</p>\n")
