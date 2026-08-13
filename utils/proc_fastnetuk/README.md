# fix_fastnetuk_ugrid

## About

The script `fix_fastnetuk_ugrid.py` is a utility for converting FastNetUK inference output stored on an unstructured UGRID mesh into CSET-compatible NetCDF files.

The primary motivation for this tool is to allow FastNetUK machine learning forecast output to be ingested into CSET alongside other forecast systems. The source files contain limited metadata, use an unstructured grid representation, and do not follow the naming conventions expected by CSET. Note that the data is actually flattened, not truly unstructured, but without explaining metadata we have to assume it is a genuine unstructured dataset.

This script performs several preprocessing steps to make the data suitable for verification and evaluation within CSET:

- Regrids unstructured UGRID data onto a regular latitude-longitude grid.
- Converts variable names to CSET/LFRic naming conventions.
- Restores appropriate units for meteorological variables.
- Creates a `forecast_period` dimension coordinate.
- Creates a scalar `forecast_reference_time` coordinate.
- Preserves valid times as a `time` auxiliary coordinate.
- Reconstructs pressure-level metadata where present.
- Saves corrected data as CSET-ready NetCDF files.

The script only performs metadata reconstruction and interpolation onto a structured grid. No scientific modifications are applied to the meteorological fields apart from unit conversions required.

> [!TIP]
> The script assumes the source file contains latitude and longitude variables describing the UGRID cell locations. These are used to reconstruct a regular latitude-longitude grid.

> [!TIP]
> On standard data from FastNetUK inference, this script requires 30GB memory to run.

## Usage

The script requires the following software to be installed:

- Python
- Iris
- NumPy
- SciPy

Run it with:

```bash
python fix_fastnetuk_ugrid.py \
    --inputpath "<input_files>" \
    --outputpath "<output_directory>"
```

### Required Arguments

- `--inputpath`: Path to one or more FastNetUK inference files. Wildcards may be used. If wildcards are used, quote the path so the shell passes the pattern to Python unchanged.
- `--outputpath`: Directory where fixed NetCDF files will be written.

## Processing Details

### UGRID Restructuring

FastNetUK inference output is stored on an unstructured mesh with latitude and longitude supplied as separate variables.

The script:

1. Extracts latitude and longitude point locations.
2. Builds a triangulation of the source mesh.
3. Creates a regular latitude-longitude target grid.
4. Interpolates each meteorological field onto the regular grid using linear interpolation.

Currently a fixed grid spacing of:

```text
0.02°
```

is used for the target grid.

> [!NOTE]
> The target grid resolution is currently inferred because the source files do not contain metadata describing the intended structured output resolution.

### Metadata Reconstruction

The source files contain limited metadata, with most information encoded within variable names.

Examples include:

```text
t_850
u_500
v_250
2t
10u
sp
```

The script extracts:

- Variable type
- Pressure level (where present)

and reconstructs metadata required by CSET.

### Forecast Coordinates

The script reconstructs forecast metadata using the source time coordinate.

It creates:

- `forecast_period`
- `forecast_reference_time`

while preserving valid times as:

- `time`

The first time value in the source file is assumed to represent forecast lead time zero.

### Pressure Levels

Variables containing pressure-level information in their names are assigned a pressure dimension coordinate.

For example:

```text
t_850
```

becomes:

```text
temperature_at_pressure_levels
pressure = 850 hPa
```

A length-one pressure dimension is created to allow future concatenation of multiple pressure levels.

### Variable Renaming

Variables are translated to CSET/LFRic naming conventions using an internal lookup table. The original names originate
from anemoi [here](https://anemoi.readthedocs.io/projects/inference/en/latest/inference/configs/outputs.html).

Examples include:

| Source Name | Output Name |
|-------------|-------------|
| t | temperature_at_pressure_levels |
| u | zonal_wind_at_pressure_levels |
| v | meridional_wind_at_pressure_levels |
| w | vertical_wind_at_pressure_levels |
| q | vapour_specific_humidity_at_pressure_levels_for_climate_averaging |
| z | geopotential_height_at_pressure_levels |
| sp | surface_air_pressure |
| 10u | eastward_wind_at_10m |
| 10v | northward_wind_at_10m |
| 2t | temperature_at_screen_level |
| 2d | dew_point_temperature_at_screen_level |
| skt | grid_surface_temperature |
| tp | surface_microphysical_rainfall_rate |

### Unit Conversion

Some variables require unit adjustments before output.

Examples include:

- Geopotential (`m² s⁻²`) → Geopotential height (`m`)
- Accumulated precipitation (`m`) → Rainfall amount (`mm 6hr⁻¹`)

These conversions are applied automatically where required.

## Examples

### 1. Process a single FastNetUK file

```bash
python fix_fastnetuk_ugrid.py \
    --inputpath "/data/fastnetuk/inference.nc" \
    --outputpath "/my/output/path"
```

Example output:

```text
/my/output/path/fixed_inference.nc
```

### 2. Process multiple files

```bash
python fix_fastnetuk_ugrid.py \
    --inputpath "/data/fastnetuk/*.nc" \
    --outputpath "/my/output/path"
```

All matching files will be processed and written to the output directory.

## Output Structure

The resulting files contain:

- Structured latitude-longitude grids
- CSET-compliant variable names
- Reconstructed units
- Forecast metadata
- Forecast period dimension
- Forecast reference time coordinate
- Valid time coordinate

Pressure-level variables will additionally contain:

```text
pressure
```

as a dimension coordinate.

## Notes

- Latitude and longitude variables must exist within the source file.
- Variables with names not present in the internal lookup table will be ignored.
- The script currently assumes a target grid spacing of approximately 0.02°.
- Linear interpolation is used to transform data from the unstructured mesh to a rectilinear grid.
- The first time value in the source file is assumed to correspond to forecast lead time zero.
- Pressure-level variables are inferred solely from the variable name.

## Owners

The following people should be contacted for queries or issues with this utility:

[jwarner8](https://github.com/jwarner8)
