#! /usr/bin/env python3

"""Fetch forecast data from a mounted filesystem."""

import os
import shutil
from pathlib import Path
from uuid import uuid4

# Create unique folder for data retrieval to prevent filename collisions.
folder = f"{os.getcwd()}/{uuid4()}"
os.mkdir(folder)
path = Path(os.getenv("FILE_PATH"))

# Pull data from file system.
if any(s in os.getenv("FILE_PATH") for s in ("*", "?")):
    local_file_path = folder
else:
    local_file_path = f"{folder}/{path.name}"
for file in path.parent.glob(path.name):
    shutil.copyfile(file, local_file_path)

# Then write out data path to "input_path" file
with open(
    f"{os.getenv('CYLC_WORKFLOW_SHARE_DIR')}/cycle/{os.getenv('CYLC_TASK_CYCLE_POINT')}/input_path",
    "wt",
    encoding="utf-8",
) as fp:
    fp.write(local_file_path)
