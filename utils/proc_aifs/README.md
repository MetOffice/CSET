# preproc_aifs

# preproc_aifs

## About

The script `preproc_aifs.py` is a utility for converting ECMWF Artificial Intelligence Forecasting System (AIFS) GRIB data into CSET-compatible NetCDF files.

The primary motivation for this tool is to allow AIFS forecasts to be ingested directly into CSET alongside other forecast systems. AIFS data is distributed as GRIB files and contains metadata conventions that differ from the naming conventions and forecast metadata expected by CSET.

This script performs several preprocessing steps to make the data suitable for verification and evaluation workflows within CSET:

- Separates GRIB messages by level type prior to conversion.
- Converts GRIB data to NetCDF using ecCodes utilities.
- Standardises variable names to match CSET/LFRic naming conventions.
- Converts units where required.
- Creates a `forecast_period` coordinate from valid times.
- Creates a scalar `forecast_reference_time` coordinate.
- Preserves valid times as a `time` auxiliary coordinate.
- Corrects ensemble metadata to use a common `realization` coordinate.
- Saves each variable to an individual NetCDF file.

No scientific modifications are made to the meteorological fields beyond unit conversions where required for consistency with CSET conventions.


> [!TIP]
> This script requires the ecCodes command-line utilities `grib_copy` and `grib_to_netcdf` to be installed and available on the system path. Otherwise, `iris` and `subprocess` are required in the python environment.



## Usage

The script requires the following software to be installed:

- Python
- Iris
- NumPy
- ECMWF ecCodes utilities (`grib_copy`, `grib_to_netcdf`)

Run it with:

```bash
python preproc_aifs.py \
    --inputpath "<input_grib_files>" \
    --forecastinit "YYYYMMDDTHHMMZ" \
    --outpath "<output_directory>"
```
> [!TIP]
> This script requires an workspace with at least 25GB of memory.

### Required Arguments

- `--inputpath`: Path to the AIFS GRIB file(s). Wildcards may be used. If a wildcard is used, quote the input path to prevent shell expansion before Python receives it.
- `--forecastinit`: Forecast initialisation timestamp used for output file naming. Typical format is `YYYYMMDDTHHMMZ`.
- `--outpath`: Directory where intermediate and final NetCDF files will be written.

## Processing Details

### GRIB Conversion

The script first splits each GRIB file into separate streams based on `typeOfLevel`:

- `isobaricInhPa`
- `heightAboveGround`
- `surface`
- `meanSea`
- `entireAtmosphere`

These extracted messages are then converted to NetCDF using `grib_to_netcdf`.

### Ensemble Handling

AIFS ensemble files contain a mixture of:

- Control forecasts
- Perturbed forecasts

The control forecast is assigned:

```text
realization = 0
```

Perturbed forecasts are assigned:

```text
realization = 1-50
```

The resulting cubes are concatenated onto a common realization dimension for compatibility with CSET workflows.

### Forecast Coordinates

The script assumes the first valid time contained within the file corresponds to forecast lead time zero.

Using this assumption it creates:

- `forecast_period`
- `forecast_reference_time`

while preserving the original valid times as:

- `time`

### Variable Renaming

Several AIFS variables are renamed to match CSET/LFRic conventions. Examples include:

| AIFS Name | Output Name |
|-----------|-------------|
| 2 metre temperature | temperature_at_screen_level |
| 2 metre dewpoint temperature | dew_point_temperature_at_screen_level |
| Mean sea level pressure | air_pressure_at_mean_sea_level |
| Total Cloud Cover | area_cloud_fraction |
| U component of wind | zonal_wind_at_pressure_levels |
| V component of wind | meridional_wind_at_pressure_levels |

Additional variables supported within the script are renamed automatically during processing.

### Unit Conversion

Some variables require unit conversion before output.

Examples include:

- Geopotential (`m² s⁻²`) → Geopototential height (`m`)
- Cloud fraction (`%`) → Fraction (`1`)

## Examples

### 1. Process a single AIFS GRIB file

```bash
python preproc_aifs.py \
    --inputpath "/data/aifs/aifs_forecast.grib2" \
    --forecastinit "20240101T0000Z" \
    --outpath "/my/output/path"
```

Example output:

```text
/my/output/path/AIFS_20240101T0000Z_temperature_at_screen_level.nc
/my/output/path/AIFS_20240101T0000Z_air_pressure_at_mean_sea_level.nc
/my/output/path/AIFS_20240101T0000Z_area_cloud_fraction.nc
...
```

### 2. Process multiple GRIB files

```bash
python preproc_aifs.py \
    --inputpath "/data/aifs/*.grib2" \
    --forecastinit "2024*101T0000Z" \
    --outpath "/my/ou*put/path"
```

All matching files will be processed and converted into individual CSET-ready NetCDF outputs.

## Notes

- The script writes temporary hidden NetCDF files to the output directo*y during GRIB processing.
- Temporary files are automatically removed*once processing is complete.
- Output is produced as one NetCDF file per variable to avoid creating excessively large combined files.
- The script assumes the first valid time in the input data corresponds to forecast lead time zero, as forecast initialisation information is not available after GRIB-to-NetCDF conversion.

## Owners
The following people should be contacted for queries or issues with this utility:

* [@jwarner8](https://github.com/jwarner8)
