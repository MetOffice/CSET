#! /usr/bin/env python3

"""Fetch forecast data from a mounted filesystem."""

import os
import shutil
from pathlib import Path
from uuid import uuid4

# Create unique folder for data retrieval to prevent filename collisions.
folder = f"{os.getcwd()}/{uuid4()}"
os.mkdir(folder)

# Pull data from file system.
source_path = Path(os.getenv("FILE_PATH"))
for file in source_path.parent.glob(source_path.name):
    print(f"Copying {file}")
    shutil.copy(file, folder + "/" + file.name)

# Then write out data path to "input_path" file
with open(
    f"{os.getenv('CYLC_WORKFLOW_SHARE_DIR')}/cycle/{os.getenv('CYLC_TASK_CYCLE_POINT')}/input_path",
    "wt",
    encoding="utf-8",
) as fp:
    fp.write(folder)
