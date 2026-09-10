# proc_fastnetuk.py

## About

The script `proc_fastnetuk.py` converts FastNetUK inference output into CSET-compatible NetCDF files.

FastNetUK output contains limited metadata and uses variable naming conventions that do not match those expected by CSET. Although the source files are described as UGRID data, the forecast fields are stored as flattened arrays representing a regular grid. This utility reshapes the flattened fields back onto a structured latitude-longitude grid.

The script performs the following preprocessing steps:

- Converts FastNetUK variable names to CSET/LFRic conventions.
- Rebuilds forecast metadata and coordinates.
- Reconstructs pressure-level information from variable names.
- Reshapes flattened fields onto the UKV latitude-longitude grid.
- Creates `forecast_period` and `forecast_reference_time` coordinates.
- Preserves valid times as a `time` auxiliary coordinate.
- Applies required unit conversions.
- Saves the result as CSET-ready NetCDF files.

No interpolation or scientific modification of the meteorological fields is performed other than the documented unit conversions.

> [!TIP]
> The script uses the grid definition stored in `ukv_mesh.nc` to reconstruct the latitude-longitude coordinates of the output data.

> [!TIP]
> Typical FastNetUK inference datasets require 30G memory due to reshaping and reconstruction of multiple variables.

## Usage

### Requirements

The script requires:

- Python
- Iris
- NumPy
- cf-units

Run with:

```bash
python fix_fastnetuk_ugrid.py \
    --inputpath "<input_files>" \
    --outputpath "<output_directory>"
```

### Required Arguments

- `--inputpath` - Input NetCDF file or wildcard pattern.
- `--outputpath` - Directory for processed output file.

If wildcards are used, quote the pattern so it is passed unchanged to Python. This script assumes each forecast is stored in one single file, and can be run on multiple files each containing a forecast.

## Processing Details

### Grid Reconstruction

FastNetUK variables are stored as flattened arrays.

The script reconstructs the original structured grid by reshaping forecast data using the dimensions:

```text
808 × 621
```

Latitude and longitude coordinates are obtained from the reference UKV mesh file:

```text
ukv_mesh.nc
```

No interpolation or regridding is performed.

### Metadata Reconstruction

Variable metadata is reconstructed from the source variable name.

Examples:

```text
t_850
u_500
v_250
2t
10u
sp
```

The script extracts:

- Variable identifier
- Pressure level (if present)

and rebuilds metadata required by CSET.

Variables that cannot be matched to the internal lookup table are skipped.

### Forecast Coordinates

Forecast metadata is reconstructed from the source time coordinate.

The following coordinates are generated:

- `forecast_reference_time`
- `forecast_period`

Valid times are retained as:

- `time`

The first time step is assumed to represent lead time zero.

### Pressure Levels

Variables containing pressure information in their name are given an explicit pressure dimension coordinate.

For example:

```text
t_850
```

becomes:

```text
temperature_at_pressure_levels
pressure = 850 hPa
```

A length-one pressure dimension is added so that multiple pressure levels can be concatenated later by Iris.

### Variable Renaming

Variables are translated to CSET/LFRic naming conventions using an internal lookup table.

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
| lsm | land_binary_mask |
| 2t | temperature_at_screen_level |
| 2d | dew_point_temperature_at_screen_level |
| skt | grid_surface_temperature |
| tp | surface_microphysical_rainfall_rate |

### Unit Conversion

The following variable-specific adjustments are performed automatically.

#### Geopotential Height

FastNetUK geopotential is converted to geopotential height:

```python
height = geopotential / 9.81
```

#### Rainfall

Rainfall fields are converted from metres to millimetres:

```python
rainfall *= 1000.0
```

## Notes

- `ukv_mesh.nc` must be available when running the script.
- Variables not present in the lookup table are ignored.
- Pressure levels are inferred solely from variable names.
- The latitude-longitude grid is reconstructed by reshaping flattened fields and not by interpolation.
- The first valid time is assumed to be forecast lead time zero.

---

## Owners

The following people should be contacted for queries or issues with this utility:

- [jwarner8](https://github.com/jwarner8)
