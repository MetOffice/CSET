#!/bin/bash

# This script provides an example of running the fetch-point-obs.py script on command-line.
#
# This script gives an example for retrieving point observations over London, UK.
# It sets up the necessary environment variables for the job, including the cycle point, analysis length, data directory, model identifier, observation subtype, retrieval interval, offset, fields to retrieve, and the geographical extent of the subarea.
# You will need to modify the paths and parameters according to your specific requirements and environment.
# Note this script will only run successfully on Met Office computing environments with python-based MetDB access.



# for explaination and format of the following exported variables, see POINT_OBSERVATIONS.md
export CYLC_TASK_CYCLE_POINT="202608003T0300Z"
export ANALYSIS_LENGTH="PT36H"
export ROSE_DATAC="/path/to/obs_output"
export MODEL_IDENTIFIER="OBS"
export OBS_SUBTYPE="['LNDSYN']"
export SURFACE_SYNOP_INTERVAL="PT1H"
export SURFACE_SYNOP_OFFSET="PT0H"
export SURFACE_SYNOP_FIELDS="['temperature_at_screen_level', 'second']"
export SUBAREA_EXTENT="(51.01, 52.22, -1.14, 0.74)"

# now run the fetch-obs-metdb.py script to retrieve the specified observation data for the defined subarea and time period.
# modify the path to the fetch-obs-metdb.py script according to your environment.

python $HOME/CSET/cset_workflow/app/fetch_obs/bin/fetch-obs-metdb.py
