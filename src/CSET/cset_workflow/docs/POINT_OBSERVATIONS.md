# fetch-obs-metdb

## About

The script `fetch-obs-metdb.py` is a utility for retrieving observations from the Met Office MetDB database, using the [MetDB python interface](http://www-mdb-apps/metdb-python/html/introduction.html).

Note this script will only run on compute environments with direct access to MetDB via python (i.e. via Met Office network).

This script will mainly be run when looking to use CSET capabilities to compare model outputs with retrieved observations, but the output of `fetch-obs-metdb.py` can be used independently to assess observations only using CSET or other utilities.

## Usage

This python script is used to support CSET workflow running when point-observations are requested.

The documentation below will detail the steps needed for running this script on the command line or a bash script, rather than via a workflow.

### Setting up the environment

Before we can run the script, we first need to set the nessessary environment variables.

First, choose an initial date and time from which to retrieve observations.
This can be in format e.g. YYYYMMDDTHHMMZ

```bash
export CYLC_TASK_CYCLE_POINT="user_defined_case_date_YYYYMMDDTHHMMZ"
```

then an ANALYSIS_LENGTH to specify the length of time over which observations should be retrieved:

```bash
export ANALYSIS_LENGTH="PT36H"
```

Choose where to store the observation output:

```bash
export ROSE_DATAC="/path/to/obs_output"
```

Then choose an identifier for the observations to be added as metadata in the output file. For example:

```bash
export MODEL_IDENTIFIER="OBS"
```

Choose the observation subtype(s) to be retrieved. This can be a list if multiple different observation types are required. For a full list see [metDB data types](http://www-mdb-apps/ssot/datatypes/index.html)). In this example, we only want to retrieve 'LNDSYN';:

```bash
export OBS_SUBTYPE="['LNDSYN']"
```

Now choose the observation retrieval interval

```bash
export SURFACE_SYNOP_INTERVAL="PT1H"
```

Now choose the offset from start time (in general suggest to leave this as PT0H):

```bash
export SURFACE_SYNOP_OFFSET="PT0H"
```

choose the surface fields for analysis
This can be a list with one or multiple elements.
Variable names are as expected by CSET to describe different model variables of interest.

```bash
export SURFACE_SYNOP_FIELDS="['first', 'second']"
 ```

To specify the region of interest, there are 2 options:

For some obs subtypes (e.g. LNDSYN, SHPSYN), it is possible to retrive by WMO block number but this is optional e.g:

```bash
export WMO_BLOCK_STTN_NMBRS="['03']"
```

Alternatively, or for obs subtypes where WMO_BLOCK_STTN_NMBR is not a valid ELEMENT_NAME, we can also set an observation region:

```bash
export SUBAREA_EXTENT="(lower_lat, upper_lat, lower_lon, upper_lon)"
```

### Run the script

Now run the scripts with, for example:

```bash
python path/to/fetch-obs-metdb.py
```

### Check outputs

To see outputs from fetch-obs-metdb.py, you can navigate to the
`/path/to/obs_output` set in exported variable ROSE_DATAC, and find output files of naming convention SUBTYPE_CASEDATE_INTERVAL.nc, with a different file generated for each SUBTYPE requested.
