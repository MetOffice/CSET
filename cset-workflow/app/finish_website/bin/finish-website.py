#! /usr/bin/env python3

"""Write finished status to website front page."""

import fcntl
import json
import os

with open(f"{os.getenv('WEB_DIR')}/status.json", "r+t") as fp:
    fcntl.flock(fp, fcntl.LOCK_EX)
    status_dict = json.load(fp)
    status_dict["status"] = "<p>Finished</p>"
    fp.seek(0)
    fp.truncate()
    json.dump(status_dict, fp)
