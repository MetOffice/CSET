# process_reanalysis

## About

The script `process_reanalysis.py` is a utility for converting atmospheric reanalysis datasets into a forecast-style format that can be directly compared with numerical weather prediction (NWP) model forecasts.

The primary motivation for this tool is to be able to analyse reanalysis alongside model forecasts in CSET, by choosing reanalysis to be the base model for verification and evaluation. CSET expects forecast data to contain forecast metadata such as:

- `forecast_reference_time`
- `forecast_period`
- `time`

Reanalysis datasets typically only contain valid time `time`, and are a series of files where the `forecast_reference_time` changes every 6 hours, and the `forecast_period` is always zero.

This script resolves this issue by transforming reanalysis data into an effective forecast representation. Rather than treating reanalysis as a special data source in CSET, the transformed output can be ingested directly into the CSET workflow. This allows reanalysis to be treated as another "model" within verification systems such as CSET.

The script currently supports datasets that can be loaded by Iris and has primarily been developed and tested using:

- ERA5 reanalysis
- Unified Model (UM) analysis data

Other model analyses may work, as only the time dimensions are manipulated, but this has not been tested.
No scientific changes are made to the meteorological fields themselves.

For each requested forecast cycle, for each variable the script:
1. Extracts the required period of time from reanalysis data.
2. Treats the start of that extraction as a forecast initialisation.
3. Generates a forecast period coordinate.
4. Generates a forecast reference time coordinate.
5. Preserves the original valid time information.
6. Saves the result as a forecast-style NetCDF file.

## Usage

The python script requires the Iris package to be present within the python install.

Run it with:

```
python process_reanalysis.py \
    --filepath "<input_files>" \
    --cyclestart YYYYMMDDTHHMMZ \
    --cycleend YYYYMMDDTHHMMZ \
    --cyclefreq <hours> \
    --forecastlength <hours> \
    --outpath "<output_directory>"
```

Required Arguments:

`--filepath`: Path to the input reanalysis data. This can be a single file or wildcard expression understood by Iris.
`--cyclestart`: First forecast initialisation time that you want the reanalysis to simulate, in format <year><month><day>T<hour><minute>Z.
--cycleend: Final forecast initialisation time, inclusive, that you want the reanalysis to simulate, in format <year><month><day>T<hour><minute>Z.

[ncgen-docs]: https://docs.unidata.ucar.edu/nug/current/netcdf_utilities_guide.html

## Owners

> [!TIP]
> Utilities must have at least one named owner.

The following people should be contacted for queries or issues with this utility:

* [@jfrost-mo](https://github.com/jfrost-mo)
