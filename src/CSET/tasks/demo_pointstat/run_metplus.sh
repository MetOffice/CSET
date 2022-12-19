#!/usr/bin/env bash

module load scitools/production-os45-1
# export PATH=${PATH}:/data/users/cfrd/MET_requirements/downloads/METplus-5.0.0-beta4/ush:/data/users/cfrd/MET_requirements/MET11.0.0Beta4/bin
# export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/lib64:/data/users/cfrd/MET_requirements/MET9/lib
export PATH=${PATH}:/data/users/cfrd/MET_requirements/downloads/METplus/ush:/data/users/cfrd/MET_requirements/MET_Dev/bin
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/usr/lib64:/data/users/cfrd/MET_requirements/MET9/lib
export ROSE_TASK_CYCLE_TIME="20220921T0300Z"
export DATESTAMP=$( rose date -c --print-f="%Y%m%d%H" )

run_metplus.py -c Pointstat_METplus_UKV.conf -c Pointstat_UKV_Areas.conf -c user_system_local.conf
