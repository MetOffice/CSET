#!/usr/bin/env bash

#############################################################################
# Wrapper script to run pointstat
#############################################################################

#no set -xeu as check errors in next task

#no set -xeu as check errors in next task
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:/data/users/cfrd/MET_requirements/MET9/lib/:/usr/lib64/:/net/project/ukmo/scitools/opt_scitools/conda/deployments/default-current/lib

#run_pointstat.py
if [[ ${AREA_STN} == "StnsPrecip" || ${AREA_STN} == "StnsSrew" || ${AREA_STN} == "UKStnsSrew" ]]; then
  if [[ ${FCASTRANGE} -lt 6 ]]; then
    echo "No need to run this step" > ${ROSE_TASK_LOG_ROOT%job}met.out
  else
    #run_metplus.py -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/${METplus_config_PS} -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/PointStat_${MODEL}_${AREA_STN}6.conf -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/PointStat_${INTERP}.conf -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/user_system_local.conf
    run_metplus.py -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/${METplus_config_PS} -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/PointStat_${MODEL}_${AREA_STN}6.conf -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/user_system_local.conf

    set -xeu

    unset LD_LIBRARY_PATH
    echo "linking METplus output logs to ${ROSE_TASK_LOG_ROOT%job}met.out"
    LINKFILE=$(ls -Art ${MET_OUTPUT}/logs | tail -n 1)
    ln -s ${MET_OUTPUT}/logs/${LINKFILE} ${ROSE_TASK_LOG_ROOT%job}met.out
    #creates a link (ln) between the MET output logs and the suite logs so that the MET logs appear in the same location and can be read in rose bush
  fi
  
elif [[ ${AREA_STN} == "StnsSrew1" ]]; then
  if [[ ${FCASTRANGE} -lt 1 ]]; then
    echo "No need to run this step" > ${ROSE_TASK_LOG_ROOT%job}met.out
  else
    run_metplus.py -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/${METplus_config_PS} -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/PointStat_${MODEL}_${AREA_STN}.conf -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/PointStat_${INTERP}.conf -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/user_system_local.conf

    set -xeu

    unset LD_LIBRARY_PATH
    echo "linking METplus output logs to ${ROSE_TASK_LOG_ROOT%job}met.out"
    LINKFILE=$(ls -Art ${MET_OUTPUT}/logs | tail -n 1)
    ln -s ${MET_OUTPUT}/logs/${LINKFILE} ${ROSE_TASK_LOG_ROOT%job}met.out
    #creates a link (ln) between the MET output logs and the suite logs so that the MET logs appear in the same location and can be read in rose bush
  fi
  
elif [[ ${AREA_STN} == "StnsPrecip12" || ${AREA_STN} == "StnsSrew12" ]]; then
  if [[ ${FCASTRANGE} -lt 12 ]]; then
    echo "No need to run this step" > ${ROSE_TASK_LOG_ROOT%job}met.out
  else
    run_metplus.py -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/${METplus_config_PS} -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/PointStat_${MODEL}_${AREA_STN}.conf -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/PointStat_${INTERP}.conf -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/user_system_local.conf

    set -xeu

    unset LD_LIBRARY_PATH
    echo "linking METplus output logs to ${ROSE_TASK_LOG_ROOT%job}met.out"
    LINKFILE=$(ls -Art ${MET_OUTPUT}/logs | tail -n 1)
    ln -s ${MET_OUTPUT}/logs/${LINKFILE} ${ROSE_TASK_LOG_ROOT%job}met.out
    #creates a link (ln) between the MET output logs and the suite logs so that the MET logs appear in the same location and can be read in rose bush
  fi
  
elif [[ ${AREA_STN} == "StnsPrecip24" || ${AREA_STN} == "StnsSrew24" ]]; then
  if [[ ${FCASTRANGE} -lt 24 ]]; then
    echo "No need to run this step" > ${ROSE_TASK_LOG_ROOT%job}met.out
  else
    run_metplus.py -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/${METplus_config_PS} -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/PointStat_${MODEL}_${AREA_STN}.conf -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/PointStat_${INTERP}.conf -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/user_system_local.conf

    set -xeu

    unset LD_LIBRARY_PATH
    echo "linking METplus output logs to ${ROSE_TASK_LOG_ROOT%job}met.out"
    LINKFILE=$(ls -Art ${MET_OUTPUT}/logs | tail -n 1)
    ln -s ${MET_OUTPUT}/logs/${LINKFILE} ${ROSE_TASK_LOG_ROOT%job}met.out
    #creates a link (ln) between the MET output logs and the suite logs so that the MET logs appear in the same location and can be read in rose bush
  fi
  
elif [[ ${AREA_STN} == "SurfaceScalar" || ${AREA_STN} == "SurfaceScalarNoHiRA" || ${AREA_STN} == "SurfaceVector" ]]; then
  run_metplus.py -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/${METplus_config_PSAll}_${AREA_STN}.conf -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/user_system_local.conf

  set -xeu

  unset LD_LIBRARY_PATH
  echo "linking METplus output logs to ${ROSE_TASK_LOG_ROOT%job}met.out"
  LINKFILE=$(ls -Art ${MET_OUTPUT}/logs | tail -n 1)
  ln -s ${MET_OUTPUT}/logs/${LINKFILE} ${ROSE_TASK_LOG_ROOT%job}met.out
  #creates a link (ln) between the MET output logs and the suite logs so that the MET logs appear in the same location and can be read in rose bush

else
  run_metplus.py -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/${METplus_config_PS} -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/PointStat_${MODEL}_${AREA_STN}.conf -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/user_system_local.conf
  #run_metplus.py -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/${METplus_config_PS} -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/PointStat_${MODEL}_${AREA_STN}.conf -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/PointStat_${INTERP}.conf -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/user_system_local.conf
  #run_metplus.py -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/${METplus_config_PS} -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/PointStat_${INTERP}.conf -c ${CYLC_SUITE_DEF_PATH}/app/${ROSE_TASK_APP}/bin/user_system_local.conf

  set -xeu

  unset LD_LIBRARY_PATH
  echo "linking METplus output logs to ${ROSE_TASK_LOG_ROOT%job}met.out"
  LINKFILE=$(ls -Art ${MET_OUTPUT}/logs | tail -n 1)
  ln -s ${MET_OUTPUT}/logs/${LINKFILE} ${ROSE_TASK_LOG_ROOT%job}met.out
  #creates a link (ln) between the MET output logs and the suite logs so that the MET logs appear in the same location and can be read in rose bush

fi

# Finally test whether or not the step returned an error or not
echo "Checking: " ${ROSE_TASK_LOG_ROOT%job}met.out
echo ""
if [[ $( grep -r "ERROR: METplus has finished running " ${ROSE_TASK_LOG_ROOT%job}met.out ) ]] ; then
  echo "  Error found within step: Check the met.out file for details"
  exit 1
else
  echo "  No errors found"
  exit 0
fi
