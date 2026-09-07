# process_reanalysis

## About

The script `process_reanalysis.py` is a utility for converting atmospheric reanalysis datasets into a forecast-style format that can be directly compared with numerical weather prediction (NWP) model forecasts.

The primary motivation for this tool is to be able to analyse reanalysis alongside model forecasts in CSET, by choosing reanalysis to be the base model for verification and evaluation. CSET expects forecast data to contain forecast metadata such as:

- `forecast_reference_time`
- `forecast_period`
- `time`

Reanalysis datasets typically only contain valid time `time`, and is a series of files where the `forecast_reference_time` changes every 6 hours, and the `forecast_period` is zero.

This script resolves this issue by transforming reanalysis data into an effective forecast representation. Rather than treating reanalysis as a special data source in CSET, the transformed output can be ingested directly into the CSET workflow. This allows reanalysis to be treated as another "model" within CSET.

The script currently supports datasets that can be loaded by Iris and has primarily been developed and tested using:

- ERA5 reanalysis
- Unified Model (UM) analysis data

Other model analyses may work, as only the time dimensions are manipulated, but this has not been tested.
No scientific changes are made to the meteorological fields themselves.

For each requested forecast cycle, for each variable found in the reanalysis the script:
1. Extracts the required period of time from reanalysis data.
2. Treats the start of that extraction as a forecast initialisation.
3. Generates a forecast period coordinate.
4. Generates a forecast reference time coordinate.
5. Preserves the original valid time information.
6. Saves the result as a forecast-style NetCDF file.

> [!TIP]
> This script does not download reanalysis data - a user must fetch this first from archive/api.

## Usage

The python script requires the Iris package to be installed and available to python.

Run it with:

```
python process_reanalysis.py \
    --files "<input_files>" \
    --cyclestart YYYYMMDDTHHMMZ" \
    --cycleend YYYYMMDDTHHMMZ" \
    --cyclefreq <hours> \
    --forecastlength <hours> \
    --outpath "<output_directory>"
```

Required Arguments:

- `--files`: Path to the input reanalysis data. This can be a single file or wildcard expression understood by Iris. If a wildcard is used, then quote the input to prevent the shell expanding the filelist as arguments to python.
- `--cyclestart`: First forecast initialisation time that you want the reanalysis to simulate, in format <year><month><day>T<hour><minute>Z.
- `--cycleend`: Final forecast initialisation time, inclusive, that you want the reanalysis to simulate, in format <year><month><day>T<hour><minute>Z.
- `--cyclefreq`: Frequency between forecast cycles, in hours, as an integer.
- `--forecastlength`: Length of the forecast you want the reanalysis to simulate, in hours, as an integer.
- `--outpath`: Path of where to store the output data. The code will write a file per forecast initialisation, in the format of `reanalysis_%Y%m%dT%H%MZ_.nc`.

## Examples

1. A single forecast that goes out to 48h, initialised on the 1st January 2024 at 00Z.

```
python process_reanalysis.py \
    --files "/data/era5/*.nc" \
    --cyclestart "20240101T0000Z" \
    --cycleend "20240101T0000Z" \
    --cyclefreq 6 \
    --forecastlength 48 \
    --outpath /my/output/path/
```
Producing one file `my/output/path/reanalysis_20240101T0000Z.nc`

2. Produce 6-hourly analysis across one day.

```
python process_reanalysis.py \
    --files "/data/era5/*.nc" \
    --cyclestart "20240101T0000Z" \
    --cycleend "20240101T1800Z" \
    --cyclefreq 6 \
    --forecastlength 48 \
    --outpath /my/output/path/
```
Produces

```
/my/output/path/reanalysis_20240101T0000Z.nc
/my/output/path/reanalysis_20240101T0600Z.nc
/my/output/path/reanalysis_20240101T1200Z.nc
/my/output/path/reanalysis_20240101T1800Z.nc
```

## Owners

The following people should be contacted for queries or issues with this utility:

* [@jwarner8](https://github.com/jwarner8)
