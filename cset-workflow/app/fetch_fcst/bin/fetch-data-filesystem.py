#! /usr/bin/env python3

"""Retrieve the files from the filesystem for the current cycle point."""

import glob
import logging
import os
import shutil

import validity_time_tester

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")

cycle_share_data_dir = f"{os.getenv('CYLC_WORKFLOW_SHARE_DIR')}/cycle/{os.getenv('CYLC_TASK_CYCLE_POINT')}/data"
os.makedirs(cycle_share_data_dir, exist_ok=True)
test_filename = validity_time_tester.create_validity_time_tester(
    pattern=os.getenv("CSET_FILE_NAME_METADATA_PATTERN"),
    validity_time=os.getenv("CYLC_TASK_CYCLE_POINT"),
    period_length=os.getenv("CSET_CYCLE_PERIOD"),
    times_per_file=int(os.getenv("CSET_TIMES_PER_FILE")),
    time_offset=int(os.getenv("CSET_FILE_TIME_OFFSET")),
)
for file in filter(test_filename, glob.iglob(os.getenv("CSET_INPUT_FILE_PATH"))):
    logging.info("Copying %s", file)
    shutil.copy(file, cycle_share_data_dir)
