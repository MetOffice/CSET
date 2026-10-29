"""Utilities for Anemoi downscaling CSET-format conversion and plotting."""

import datetime as dt
import json
import warnings
from pathlib import Path

import cf_units
import iris
import numpy as np
from iris.warnings import IrisGuessBoundsWarning

import CSET.operators.plot as cset_plot
import CSET.operators.read as cset_read
from CSET._common import filename_slugify

_CUBE_CACHE: dict[tuple[str, str], iris.cube.Cube] = {}
_REF_GRID_COORDS: tuple[np.ndarray, np.ndarray] | None = None

"""Convert Paris Anemoi outputs into CSET-style per-forecast NetCDF files.

How to run
----------
1) Use the CSET conda environment:

    conda activate /data/users/lewis.blunn/.conda/envs/cset-dev

2) Run from the cset_workflow directory:

    cd /home/users/lewis.blunn/CSET/src/CSET/cset_workflow
    python ai_downscaling_conversion/plot_urban_ML_CSET_Anemoi_Paris.py

Alternative (without activating):

    conda run -p /data/users/lewis.blunn/.conda/envs/cset-dev --no-capture-output \
         python ai_downscaling_conversion/plot_urban_ML_CSET_Anemoi_Paris.py

Notes
-----
- This script expects xarray+zarr available in the chosen environment.
- It hard-fails if conditioning-source dates do not match predictions.nc dates.
- Set `process`/`plot` flags below depending on whether you want conversion,
  plotting, or both.
- Saved CSET workflow NetCDFs are strict and keep only `target_realizations`.
- Plots can be generated from all available realizations, with saved members
    labelled in postage-stamp titles.
"""

# Keep stdout clean when Iris falls back to guessed contiguous bounds.
warnings.filterwarnings("ignore", category=IrisGuessBoundsWarning)

process = True
plot = True
plot_from_all_realizations = True

# Fast-run controls for debugging/iteration speed.
# Set `selected_frt_timestamps = []` to save all available FRTs while still
# plotting just one chosen FRT via `frt_timestamp` below.
# Use a non-empty list to limit both saved and plot-prepared cubes.
selected_frt_timestamps = []  # for specific forecast reference times do e.g., ["20240719210000"]
# Plot exactly this forecast_reference_time when plot=True.
plot_frt_timestamp = "20240719210000"
max_time_steps_per_frt = None

# Variables intended for this workflow.
# These lists are declarative (for clarity and future extension); the script
# currently runs one variable at a time via `varname` below.
variables_to_process = [
    "surface_microphysical_rainfall_rate",
    "wind_speed_at_10m",
    "temperature_at_screen_level",
    "visibility_in_air",
]
variables_to_plot = list(variables_to_process)
variables_to_save = list(variables_to_process)

# Input/output locations for Paris Anemoi data.
BASE_DIR = Path("/data/users/lewis.blunn/machine_learning/CSET/paris_anemoi_Q4_2026")
PREDICTIONS_FILE = BASE_DIR / "predictions.nc"
CONDITIONING_SOURCE = Path(
    "/data/users/lmtrials/unified_pipeline/datasets/urban_downscaling/paris_64x64/anemoi_zarr/val/paris-lres-pred-summer-downscaling-64x64-val-1h-v1.zarr"
)

output_data_dir = BASE_DIR / "ml_data_cset_paris"
output_figs_dir = Path(__file__).resolve().parent / "figs"

# Merge sample + realization to a single realization identifier for CSET plotting.
merge_input_sample = True

# Keep a common 3-member realization set so inter-model difference/score recipes
# can broadcast against the 300m baseline.
# Rationale: this preserves member correspondence across 300m/ML/2.2km and, with
# current input layout, effectively uses the first ML sample for each matched
# driving member. This is intentionally strict (hard-fail if missing members)
# rather than flexible, because CSET comparison operators expect aligned shapes.
# NOTE: Saved NetCDF outputs for the CSET workflow are intentionally restricted
# to these aligned members.
target_realizations = np.array([100, 110, 120], dtype=int)

# CSET target variable (single-variable execution).
varname = "surface_microphysical_rainfall_rate"


def _source_spec(path: Path, variable: str, suffix: str) -> tuple[Path, str, str]:
    return (path, variable, suffix)


def _load_cube(path: Path, variable: str) -> iris.cube.Cube:
    cache_key = (str(path), variable)
    if cache_key in _CUBE_CACHE:
        return _CUBE_CACHE[cache_key].copy()

    if path.suffix == ".zarr":
        try:
            import xarray as xr
        except ImportError as err:
            raise ImportError(
                "xarray is required to load zarr inputs. "
                "Install xarray+zarr or run in an environment that includes them."
            ) from err

        # Try both non-consolidated and consolidated metadata layouts.
        open_errors = []
        for consolidated in (False, True):
            try:
                ds = xr.open_zarr(path, consolidated=consolidated)

                if variable in ds.data_vars:
                    cube = ds[variable].to_iris()
                    _CUBE_CACHE[cache_key] = cube
                    return cube.copy()

                # Anemoi zarr layout: data(time, variable, ensemble, cell)
                # with variable names stored under attrs["variables"].
                packed_vars = list(ds.attrs.get("variables", []))
                if "data" not in ds.data_vars or variable not in packed_vars:
                    available = sorted(ds.data_vars)
                    named = sorted(packed_vars)
                    raise ValueError(
                        f"'{variable}' not found in {path}. "
                        f"Available data_vars: {available}. "
                        f"Available packed variables: {named}"
                    )

                var_idx = packed_vars.index(variable)
                da = ds["data"].isel(variable=var_idx, drop=True)

                if "ensemble" in da.dims:
                    da = da.rename({"ensemble": "ensemble_member"})

                # Preserve ensemble as an explicit coordinate so Iris keeps it
                # available for realization promotion later.
                if "ensemble_member" in da.dims and "ensemble_member" not in da.coords:
                    da = da.assign_coords(
                        ensemble_member=(
                            "ensemble_member",
                            np.arange(da.sizes["ensemble_member"], dtype=np.int32),
                        )
                    )

                if "dates" in ds.data_vars and "time" in da.dims:
                    da = da.assign_coords(
                        time=(
                            "time",
                            np.asarray(ds["dates"].values, dtype="datetime64[ns]"),
                        )
                    )

                if "cell" in da.dims:
                    # Expand flattened cell layout back to a 2D grid expected
                    # by CSET plotting and diagnostics.
                    field_shape = ds.attrs.get("field_shape")
                    if not (
                        isinstance(field_shape, (list, tuple)) and len(field_shape) == 2
                    ):
                        raise ValueError(
                            f"Missing/invalid field_shape in {path}: {field_shape}"
                        )

                    n_lat = int(field_shape[0])
                    n_lon = int(field_shape[1])
                    if da.sizes["cell"] != n_lat * n_lon:
                        raise ValueError(
                            "Cell size does not match field_shape for "
                            f"{path}: cell={da.sizes['cell']} field_shape={field_shape}"
                        )

                    if da.dims[-1] != "cell":
                        raise ValueError(
                            f"Unsupported Anemoi data layout (cell must be last): {da.dims}"
                        )

                    arr = np.asarray(da.values).reshape(*da.shape[:-1], n_lat, n_lon)
                    new_dims = tuple(d for d in da.dims if d != "cell") + (
                        "grid_latitude",
                        "grid_longitude",
                    )
                    coords = {
                        d: da.coords[d].values
                        for d in da.dims
                        if d != "cell" and d in da.coords
                    }

                    if "latitudes" in ds.data_vars and "longitudes" in ds.data_vars:
                        lat = np.asarray(ds["latitudes"].values).reshape(n_lat, n_lon)
                        lon = np.asarray(ds["longitudes"].values).reshape(n_lat, n_lon)
                        coords["grid_latitude"] = lat[:, 0]
                        coords["grid_longitude"] = lon[0, :]
                    else:
                        coords["grid_latitude"] = np.arange(n_lat, dtype=np.float64)
                        coords["grid_longitude"] = np.arange(n_lon, dtype=np.float64)

                    da = xr.DataArray(
                        arr,
                        dims=new_dims,
                        coords=coords,
                        attrs=dict(da.attrs),
                        name=variable,
                    )
                else:
                    da = da.rename(variable)

                cube = da.to_iris()
                _CUBE_CACHE[cache_key] = cube
                return cube.copy()
            except (OSError, RuntimeError, ValueError, TypeError, KeyError) as err:
                open_errors.append(
                    f"consolidated={consolidated}: {type(err).__name__}: {err}"
                )

        raise RuntimeError("Failed to load zarr source. " + " | ".join(open_errors))

    try:
        cube = iris.load_cube(path, variable)
        _CUBE_CACHE[cache_key] = cube
        return cube.copy()
    except Exception as err:
        available = sorted(
            {
                c.standard_name or c.long_name or c.var_name
                for c in iris.load(path)
                if (c.standard_name or c.long_name or c.var_name) is not None
            }
        )
        raise ValueError(
            f"'{variable}' is not available in {path}; available variables: {available}."
        ) from err


def _get_reference_grid_coords() -> tuple[np.ndarray, np.ndarray]:
    global _REF_GRID_COORDS
    if _REF_GRID_COORDS is not None:
        return _REF_GRID_COORDS

    ref_cube = _load_cube(PREDICTIONS_FILE, "target_pr")
    lat = np.asarray(ref_cube.coord("grid_latitude").points, dtype=np.float64).copy()
    lon = np.asarray(ref_cube.coord("grid_longitude").points, dtype=np.float64).copy()
    _REF_GRID_COORDS = (lat, lon)
    return _REF_GRID_COORDS


def _apply_reference_grid_coords(cube: iris.cube.Cube) -> None:
    if not (cube.coords("grid_latitude") and cube.coords("grid_longitude")):
        return

    ref_lat, ref_lon = _get_reference_grid_coords()
    lat_coord = cube.coord("grid_latitude")
    lon_coord = cube.coord("grid_longitude")

    if len(lat_coord.points) == len(ref_lat):
        lat_coord.points = ref_lat.copy()
    if len(lon_coord.points) == len(ref_lon):
        lon_coord.points = ref_lon.copy()


def _load_fake_date_mapping(mapping_path: Path) -> dict:
    # Mapping is generated by upstream fake-date preprocessing and links each
    # fake timestamp to both true_time and forecast_reference_time.
    with open(mapping_path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)

    if not isinstance(raw, list) or not raw:
        raise ValueError(f"Mapping file is empty or invalid: {mapping_path}")

    required = {"fake_time", "true_time", "forecast_reference_time"}
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            raise TypeError(f"Mapping entry {idx} is not an object in {mapping_path}")
        missing = required.difference(item)
        if missing:
            raise ValueError(
                f"Mapping entry {idx} in {mapping_path} is missing keys: {sorted(missing)}"
            )

    fake = np.array([item["fake_time"] for item in raw], dtype="datetime64[ns]")
    true = np.array([item["true_time"] for item in raw], dtype="datetime64[ns]")
    frt = np.array(
        [item["forecast_reference_time"] for item in raw], dtype="datetime64[ns]"
    )

    keys = fake.astype("int64").tolist()
    return {
        "fake_to_true": dict(zip(keys, true, strict=True)),
        "fake_to_frt": dict(zip(keys, frt, strict=True)),
    }


def _to_ns_keys(values) -> np.ndarray:
    """Convert datetime-like values to integer nanosecond keys."""
    out = []
    for value in values:
        # Works for datetime.datetime/cftime-like objects returned by Iris.
        out.append(np.datetime64(str(value)).astype("datetime64[ns]").astype("int64"))
    return np.array(out, dtype=np.int64)


def _restore_fake_dates_if_needed(
    cube: iris.cube.Cube, source_path: Path
) -> iris.cube.Cube:
    """Restore real times for Anemoi fake-dated zarr inputs.

    Requires a fake_date_mapping.json next to the zarr store and fails hard if
    any cube time points are not represented in that mapping.
    """
    if source_path.suffix != ".zarr":
        return cube

    mapping_path = source_path.parent / "fake_date_mapping.json"
    if not mapping_path.exists():
        raise FileNotFoundError(
            f"Missing fake date mapping file for zarr input: {mapping_path}"
        )

    if not cube.coords("time"):
        raise ValueError(f"No 'time' coordinate found in zarr cube from {source_path}")

    mapping = _load_fake_date_mapping(mapping_path)
    time_coord = cube.coord("time")

    # Translate current fake time points to mapping keys.
    fake_keys = _to_ns_keys(time_coord.units.num2date(time_coord.points))
    missing = [int(k) for k in fake_keys if int(k) not in mapping["fake_to_true"]]
    if missing:
        raise ValueError(
            f"Found {len(missing)} timesteps not present in {mapping_path}; "
            f"first missing key: {missing[0]}"
        )

    # Resolve fake timestamps to their real-world time and FRT values.
    true_times = np.array(
        [mapping["fake_to_true"][int(k)] for k in fake_keys], dtype="datetime64[ns]"
    )
    frt_times = np.array(
        [mapping["fake_to_frt"][int(k)] for k in fake_keys], dtype="datetime64[ns]"
    )

    # Keep original time DimCoord order and carry restored true_time as an
    # AuxCoord; per-forecast slices will apply it as the canonical time axis.
    time_dim = cube.coord_dims("time")[0]

    # Build restored true_time as a numeric time coordinate.
    time_units = cf_units.Unit("hours since 1970-01-01 00:00:00", calendar="standard")
    py_true = [
        dt.datetime.fromtimestamp(
            int(t.astype("datetime64[s]").astype(np.int64)),
            dt.UTC,
        )
        for t in true_times
    ]
    true_points = np.asarray(time_units.date2num(py_true), dtype=np.float64)

    if cube.coords("true_time"):
        cube.remove_coord("true_time")

    cube.add_aux_coord(
        iris.coords.AuxCoord(
            true_points,
            long_name="true_time",
            units=time_units,
        ),
        data_dims=(time_dim,),
    )

    # Replace forecast_reference_time as a time-aligned AuxCoord.
    frt_units = cf_units.Unit(
        "days since 1970-01-01 00:00:00",
        calendar="proleptic_gregorian",
    )
    py_frt = [
        dt.datetime.fromtimestamp(
            int(t.astype("datetime64[s]").astype(np.int64)),
            dt.UTC,
        )
        for t in frt_times
    ]
    frt_points = np.asarray(frt_units.date2num(py_frt), dtype=np.float64)

    if cube.coords("forecast_reference_time"):
        cube.remove_coord("forecast_reference_time")

    cube.add_aux_coord(
        iris.coords.AuxCoord(
            frt_points,
            standard_name="forecast_reference_time",
            long_name="forecast_reference_time",
            units=frt_units,
        ),
        data_dims=(time_dim,),
    )

    return cube


def _frt_ns_keys(cube: iris.cube.Cube) -> np.ndarray:
    # Use integer nanosecond keys for robust cross-file FRT set comparisons.
    frt_coord = cube.coord("forecast_reference_time")
    frt_dates = frt_coord.units.num2date(np.asarray(frt_coord.points, dtype=np.float64))
    return _to_ns_keys(frt_dates)


def _ns_key_to_label(ns_key: int) -> str:
    ts = np.datetime64(int(ns_key), "ns")
    return str(ts).replace("T", " ")


def _normalise_frt(cube: iris.cube.Cube) -> None:
    frt_coord = cube.coord("forecast_reference_time")
    frt_target_units = cf_units.Unit(
        "days since 1970-01-01 00:00:00",
        calendar="proleptic_gregorian",
    )

    if frt_coord.units.is_unknown():
        # Common pattern: raw integer nanoseconds from unix epoch.
        frt_coord.points = (
            np.round(
                (
                    np.asarray(frt_coord.points, dtype=np.float64)
                    / (1_000_000_000.0 * 86400.0)
                )
                * 86400.0
            )
            / 86400.0
        )
        frt_coord.units = frt_target_units
        return

    frt_coord.points = (
        np.round(
            frt_target_units.date2num(
                frt_coord.units.num2date(np.asarray(frt_coord.points, dtype=np.float64))
            )
            * 86400.0
        )
        / 86400.0
    )
    frt_coord.units = frt_target_units


def _normalise_offset(cube: iris.cube.Cube) -> None:
    if not cube.coords("forecast_reference_offset"):
        return

    offset_coord = cube.coord("forecast_reference_offset")
    if str(offset_coord.units) == "nanoseconds":
        offset_coord.convert_units("hours")
    elif str(offset_coord.units) != "hours":
        raise ValueError(
            f"Unsupported forecast_reference_offset units: {offset_coord.units}"
        )


def _promote_realization(td: iris.cube.Cube) -> iris.cube.Cube:
    # Normalise different source conventions onto a single 'realization' axis.
    if td.coords("realization") and td.coord_dims("realization"):
        return td

    if td.coords("ensemble_member") and td.coord_dims("ensemble_member"):
        dim = td.coord_dims("ensemble_member")[0]
        points = np.asarray(td.coord("ensemble_member").points).astype(int)
        td.remove_coord("ensemble_member")
        td.add_dim_coord(
            iris.coords.DimCoord(points, long_name="realization", units="1"),
            dim,
        )
        return td

    if td.coords("input") and td.coord_dims("input"):
        dim = td.coord_dims("input")[0]
        points = np.asarray(td.coord("input").points)
        try:
            points_int = points.astype(int)
        except ValueError:
            # Stable integer encoding for non-numeric input labels.
            labels = [str(p) for p in points]
            uniq = {label: i + 1 for i, label in enumerate(sorted(set(labels)))}
            points_int = np.array([uniq[label] for label in labels], dtype=int)

        td.remove_coord("input")
        td.add_dim_coord(
            iris.coords.DimCoord(points_int, long_name="realization", units="1"),
            dim,
        )
        return td

    raise ValueError(
        "Cannot identify realization axis: expected one of realization, "
        "ensemble_member, or input as a dimension coordinate."
    )


def _ensure_xy_bounds(cube: iris.cube.Cube) -> None:
    for coord_name in ("grid_latitude", "grid_longitude"):
        if cube.coords(coord_name) and not cube.coord(coord_name).has_bounds():
            cube.coord(coord_name).guess_bounds()


def _frt_ref_to_timestamp(ref_value: float, units: cf_units.Unit) -> str:
    dt_str = units.title(ref_value)
    return filename_slugify(dt_str)


def _limit_time_steps(cube: iris.cube.Cube) -> iris.cube.Cube:
    if max_time_steps_per_frt is None:
        return cube
    if not cube.coords("time"):
        return cube

    time_dim = cube.coord_dims("time")
    if not time_dim:
        return cube

    tdim = time_dim[0]
    if cube.shape[tdim] <= max_time_steps_per_frt:
        return cube

    slicer = [slice(None)] * cube.ndim
    slicer[tdim] = slice(0, max_time_steps_per_frt)
    return cube[tuple(slicer)]


def _ensure_standard_dim_order(cube: iris.cube.Cube) -> iris.cube.Cube:
    """Reorder to realization,time,y,x when those dimensions exist.

    CSET difference/score operators assume compatible underlying data layout
    between models, so we normalize dimensional ordering explicitly.
    """
    target_names = ["realization", "time", "grid_latitude", "grid_longitude"]
    if not all(cube.coords(name) and cube.coord_dims(name) for name in target_names):
        return cube

    target_order = [cube.coord_dims(name)[0] for name in target_names]
    if target_order != list(range(cube.ndim)):
        cube.transpose(target_order)
    return cube


def _normalise_grid_longitude_range(cube: iris.cube.Cube) -> None:
    """Force a consistent longitude convention across models.

    Using a single range avoids xarray alignment dropping all points when one
    source uses [0, 360) and another uses [-180, 180).
    """
    if not cube.coords("grid_longitude"):
        return

    lon = cube.coord("grid_longitude")
    points = np.asarray(lon.points, dtype=np.float64)
    lon.points = ((points + 180.0) % 360.0) - 180.0

    if lon.has_bounds():
        bounds = np.asarray(lon.bounds, dtype=np.float64)
        lon.bounds = ((bounds + 180.0) % 360.0) - 180.0


def _subset_target_realizations(cube: iris.cube.Cube) -> iris.cube.Cube:
    if not cube.coords("realization"):
        return cube

    current = np.asarray(cube.coord("realization").points).astype(int)
    keep = [r for r in target_realizations if r in set(current.tolist())]
    if len(keep) != len(target_realizations):
        raise ValueError(
            f"Cube is missing target realizations. expected={target_realizations.tolist()} "
            f"found={current.tolist()}"
        )

    keep_set = {int(v) for v in keep}
    return cube.extract(
        iris.Constraint(realization=lambda cell: int(cell.point) in keep_set)
    )


def _extract_frt_cube(cubes: iris.cube.CubeList, frt_timestamp: str) -> iris.cube.Cube:
    frt_dt = dt.datetime.strptime(frt_timestamp, "%Y%m%d%H%M%S")
    target_slug = filename_slugify(frt_dt.strftime("%Y-%m-%d %H:%M:%S"))

    for cube in cubes:
        seq_coord = cube.coord("forecast_reference_time")
        cube_slug = filename_slugify(seq_coord.units.title(seq_coord.points[0]))
        if cube_slug == target_slug:
            return cube

    available = []
    for cube in cubes:
        seq_coord = cube.coord("forecast_reference_time")
        available.append(filename_slugify(seq_coord.units.title(seq_coord.points[0])))

    raise ValueError(
        f"Requested forecast {frt_timestamp} not found. Available forecasts: {available}"
    )


def _convert_source(
    path: Path,
    source_varname: str,
    model_suffix: str,
    expected_frt_keys: np.ndarray | None = None,
    subset_target_realizations: bool = True,
    save_outputs: bool = True,
    apply_reference_grid_coords: bool = True,
) -> iris.cube.CubeList:
    print(
        f"\n=== Processing source variable: {source_varname} ({model_suffix}) from {path} ==="
    )

    # Load and standardise each source into a common CSET-friendly cube.
    data = _load_cube(path, source_varname)
    data = _restore_fake_dates_if_needed(data, path)

    if varname == "surface_microphysical_rainfall_rate":
        original_units = str(data.units)
        data = data * 3600.0
        data.units = cf_units.Unit("mm h-1")
        print(f"Adjusted units: {original_units} -> {data.units}")
    elif varname == "wind_speed_at_10m":
        original_units = str(data.units)
        if original_units == "m.s-1" or original_units in ("unknown", "1"):
            data.units = cf_units.Unit("m s-1")
        print(f"Adjusted units: {original_units} -> {data.units}")
    elif varname == "temperature_at_screen_level":
        original_units = str(data.units)
        if original_units in ("unknown", "1"):
            data.units = cf_units.Unit("K")
        print(f"Adjusted units: {original_units} -> {data.units}")
    elif varname == "visibility_in_air":
        original_units = str(data.units)
        if original_units in ("unknown", "1"):
            data.units = cf_units.Unit("m")
        print(f"Adjusted units: {original_units} -> {data.units}")

    data.rename(varname)
    if apply_reference_grid_coords:
        _apply_reference_grid_coords(data)

    _normalise_frt(data)
    _normalise_offset(data)

    if expected_frt_keys is not None:
        # Hard-fail unless this source has the same forecast cycles as the
        # reference predictions.nc data.
        data_frt_keys = _frt_ns_keys(data)
        unique_data_keys = np.unique(data_frt_keys)
        expected_keys = np.unique(expected_frt_keys.astype(np.int64))

        data_key_set = {int(k) for k in unique_data_keys}
        expected_key_set = {int(k) for k in expected_keys}
        missing = sorted(expected_key_set - data_key_set)
        extra = sorted(data_key_set - expected_key_set)

        if missing or extra:
            missing_txt = [_ns_key_to_label(k) for k in missing[:5]]
            extra_txt = [_ns_key_to_label(k) for k in extra[:5]]
            raise ValueError(
                f"forecast_reference_time mismatch for {path}. "
                f"missing={missing_txt} extra={extra_txt} "
                f"(expected {len(expected_keys)} unique values, found {len(unique_data_keys)})."
            )

    frt_coord = data.coord("forecast_reference_time")
    frt_target_units = cf_units.Unit(
        "days since 1970-01-01 00:00:00",
        calendar="proleptic_gregorian",
    )
    frt_points = np.asarray(frt_coord.points, dtype=np.float64)
    frt_dim = data.coord_dims("forecast_reference_time")[0]

    cubelist = iris.cube.CubeList()
    # Split into one output cube per forecast_reference_time.
    for ref in np.unique(frt_points):
        ref_timestamp = _frt_ref_to_timestamp(float(ref), frt_target_units)
        if selected_frt_timestamps and ref_timestamp not in selected_frt_timestamps:
            continue

        idx = np.where(np.isclose(frt_points, ref))[0]
        if idx.size == 0:
            continue

        slicer = [slice(None)] * data.ndim
        slicer[frt_dim] = idx
        td = data[tuple(slicer)]

        frt = td.coord("forecast_reference_time").collapsed()
        frt.points = np.array([float(ref)], dtype=np.float64)
        if frt.has_bounds():
            frt.bounds = np.array([[float(ref), float(ref)]], dtype=np.float64)
        frt.units = frt_target_units

        td.remove_coord("forecast_reference_time")
        td.add_aux_coord(frt)

        if td.coords("true_time"):
            # For fake-date sources, convert time axis to true_time within each
            # forecast slice and enforce strict monotonicity for Iris DimCoord.
            true_time = td.coord("true_time")
            true_points = np.asarray(true_time.points, dtype=np.float64)
            if true_points.size > 1 and np.any(np.diff(true_points) <= 0):
                raise ValueError(
                    "Mapped true_time is not strictly increasing within a "
                    f"forecast slice for {path} at forecast_reference_time={ref}."
                )

            time_coord = td.coord("time")
            time_coord.points = true_points
            time_coord.units = true_time.units
            td.remove_coord("true_time")

        iris.util.promote_aux_coord_to_dim_coord(td, "time")
        td = cset_read._grid_longitude_fix_callback(td)
        td = _promote_realization(td)

        has_sample_dim = td.coords("sample") and bool(td.coord_dims("sample"))

        if merge_input_sample and has_sample_dim:
            # ML outputs carry both realization and sample dimensions; encode
            # both into a single realization index used downstream by CSET.
            merged = iris.cube.CubeList()
            for realization in td.coord("realization").points:
                tdi = td.extract(iris.Constraint(realization=realization))
                xx_base = int(realization) + 10
                sample_vals = np.asarray(tdi.coord("sample").points).astype(int)
                tdi.coord("sample").points = xx_base * 10 + sample_vals
                tdi.remove_coord("realization")
                if tdi.coords("forecast_reference_offset"):
                    tdi.remove_coord("forecast_reference_offset")
                _ensure_xy_bounds(tdi)
                merged.append(tdi)

            merged_cube = merged.concatenate_cube()
            sample_dim = merged_cube.coord_dims("sample")[0]
            sample_points = np.asarray(merged_cube.coord("sample").points).astype(int)
            merged_cube.remove_coord("sample")
            merged_cube.add_dim_coord(
                iris.coords.DimCoord(sample_points, long_name="realization", units="1"),
                sample_dim,
            )
            if subset_target_realizations:
                merged_cube = _subset_target_realizations(merged_cube)
            merged_cube = _limit_time_steps(merged_cube)
            merged_cube = _ensure_standard_dim_order(merged_cube)
            if apply_reference_grid_coords:
                _apply_reference_grid_coords(merged_cube)
            if merged_cube.long_name is None:
                merged_cube.long_name = varname
            cubelist.append(merged_cube)
        else:
            # Keep one realization axis for sources without a sample dimension.
            td.coord("realization").points = (
                np.asarray(td.coord("realization").points).astype(int) + 10
            ) * 10
            if subset_target_realizations:
                td = _subset_target_realizations(td)
            _ensure_xy_bounds(td)
            td = _limit_time_steps(td)
            td = _ensure_standard_dim_order(td)
            if apply_reference_grid_coords:
                _apply_reference_grid_coords(td)
            if td.long_name is None:
                td.long_name = varname
            cubelist.append(td)

    if save_outputs:
        output_data_dir.mkdir(parents=True, exist_ok=True)
        for cube in cubelist:
            _normalise_grid_longitude_range(cube)
            seq_coord = cube.coord("forecast_reference_time")
            subdir = filename_slugify(seq_coord.units.title(seq_coord.points[0]))
            save_filename = output_data_dir / f"{cube.name()}{model_suffix}_{subdir}.nc"
            print(f"Saving cube to: {save_filename}")
            iris.save(cube, save_filename)

    return cubelist


def _get_model_sources(selected_varname: str) -> list[tuple[Path, str, str]]:
    if not CONDITIONING_SOURCE.exists():
        raise FileNotFoundError(
            f"Conditioning source does not exist: {CONDITIONING_SOURCE}"
        )

    if selected_varname == "surface_microphysical_rainfall_rate":
        return [
            _source_spec(PREDICTIONS_FILE, "pred_pr", "_ML"),
            _source_spec(PREDICTIONS_FILE, "target_pr", "_0p3km"),
            _source_spec(CONDITIONING_SOURCE, "pr", "_2p2km"),
        ]
    if selected_varname == "wind_speed_at_10m":
        return [
            _source_spec(PREDICTIONS_FILE, "pred_ws", "_ML"),
            _source_spec(PREDICTIONS_FILE, "target_ws", "_0p3km"),
            _source_spec(CONDITIONING_SOURCE, "wind", "_2p2km"),
        ]
    if selected_varname == "temperature_at_screen_level":
        return [
            _source_spec(PREDICTIONS_FILE, "pred_tas", "_ML"),
            _source_spec(PREDICTIONS_FILE, "target_tas", "_0p3km"),
            _source_spec(CONDITIONING_SOURCE, "tas", "_2p2km"),
        ]
    if selected_varname == "visibility_in_air":
        return [
            _source_spec(PREDICTIONS_FILE, "pred_vis", "_ML"),
            _source_spec(PREDICTIONS_FILE, "target_vis", "_0p3km"),
            # Use visibility including precipitation (vis), not visnopr.
            _source_spec(CONDITIONING_SOURCE, "vis", "_2p2km"),
        ]

    raise ValueError(f"Unsupported varname '{selected_varname}'.")


if plot:
    # Avoid creating metadata sidecar files (meta.json / index.html) when this
    # script is run standalone outside the recipe runner.
    _orig_get_recipe_metadata = cset_plot.get_recipe_metadata
    _orig_append_to_plot_index = cset_plot._append_to_plot_index
    _orig_make_plot_html_page = cset_plot._make_plot_html_page
    _orig_set_postage_stamp_title = cset_plot._set_postage_stamp_title
    _orig_colorbar_map_levels = cset_plot.colorbar_map_levels

    cset_plot.get_recipe_metadata = dict
    cset_plot._append_to_plot_index = lambda plot_index: plot_index
    cset_plot._make_plot_html_page = lambda plots: None

    def _dynamic_colorbar_map_levels(cube: iris.cube.Cube, axis=None):
        """Dynamic plotting limits for standalone runs.

        - Keep precipitation on CSET defaults.
        - For other variables, use data min/max.
        - For wind speed, enforce a hard zero floor.
        """
        if cube.name() == "surface_microphysical_rainfall_rate":
            return _orig_colorbar_map_levels(cube, axis=axis)

        cmap, _, _ = _orig_colorbar_map_levels(cube, axis=axis)

        data = np.ma.asarray(cube.data)
        finite = np.ma.masked_invalid(data)
        if finite.count() == 0:
            return _orig_colorbar_map_levels(cube, axis=axis)

        vmin = float(finite.min())
        vmax = float(finite.max())

        if cube.name() == "wind_speed_at_10m":
            vmin = 0.0

        if vmax <= vmin:
            vmax = vmin + 1e-6

        levels = np.linspace(vmin, vmax, 51)
        return cmap, levels, None

    cset_plot.colorbar_map_levels = _dynamic_colorbar_map_levels

    # Hard-disable sidecars for standalone runs.
    Path("meta.json").unlink(missing_ok=True)
    Path("index.html").unlink(missing_ok=True)

    # Label members used by strict workflow outputs when plotting all members.
    saved_member_set = {int(v) for v in target_realizations.tolist()}

    def _set_postage_stamp_title_highlight(stamp_coord: iris.coords.Coord) -> str:
        title = _orig_set_postage_stamp_title(stamp_coord)
        if stamp_coord.name() != "realization":
            return title
        try:
            member = int(stamp_coord.points[0])
        except (TypeError, ValueError):
            return title
        return f"{title} [saved]" if member in saved_member_set else title

    cset_plot._set_postage_stamp_title = _set_postage_stamp_title_highlight

selected_variables = [v for v in variables_to_process if v in variables_to_save]
if not selected_variables:
    selected_variables = [varname]

# Use predictions.nc as the reference date set for strict FRT matching.
pred_ref = _load_cube(PREDICTIONS_FILE, "pred_pr")
_normalise_frt(pred_ref)
expected_frt_keys = np.unique(_frt_ns_keys(pred_ref))

try:
    for selected_varname in selected_variables:
        print(f"\n=== Running variable: {selected_varname} ===")
        varname = selected_varname
        model_sources = _get_model_sources(selected_varname)

        if process:
            produced = {}
            for source_path, source_varname, suffix in model_sources:
                required_frt = expected_frt_keys if suffix == "_2p2km" else None
                produced[suffix] = _convert_source(
                    source_path,
                    source_varname,
                    suffix,
                    expected_frt_keys=required_frt,
                )

        if plot and selected_varname in variables_to_plot:
            if plot_from_all_realizations:
                plot_produced = {}
                for source_path, source_varname, suffix in model_sources:
                    required_frt = expected_frt_keys if suffix == "_2p2km" else None
                    plot_produced[suffix] = _convert_source(
                        source_path,
                        source_varname,
                        suffix,
                        expected_frt_keys=required_frt,
                        subset_target_realizations=False,
                        save_outputs=False,
                        apply_reference_grid_coords=False,
                    )

                cube_ml = _extract_frt_cube(plot_produced["_ML"], plot_frt_timestamp)
                cube_ref = _extract_frt_cube(
                    plot_produced["_0p3km"], plot_frt_timestamp
                )
                cube_cond = _extract_frt_cube(
                    plot_produced["_2p2km"], plot_frt_timestamp
                )
            else:
                _frt_dt = dt.datetime.strptime(plot_frt_timestamp, "%Y%m%d%H%M%S")
                _subdir = filename_slugify(_frt_dt.strftime("%Y-%m-%d %H:%M:%S"))

                cube_ml = iris.load_cube(
                    output_data_dir / f"{selected_varname}_ML_{_subdir}.nc"
                )
                cube_ref = iris.load_cube(
                    output_data_dir / f"{selected_varname}_0p3km_{_subdir}.nc"
                )
                cube_cond = iris.load_cube(
                    output_data_dir / f"{selected_varname}_2p2km_{_subdir}.nc"
                )

            cubes_to_plot = [
                ("_ML", cube_ml),
                ("_0p3km", cube_ref),
                ("_2p2km", cube_cond),
            ]
            for suffix, plot_cube in cubes_to_plot:
                if plot_cube.long_name is None:
                    plot_cube.long_name = plot_cube.name()
                seq_coord = plot_cube.coord("forecast_reference_time")
                subdir = filename_slugify(seq_coord.units.title(seq_coord.points[0]))
                plotdir = output_figs_dir / subdir
                # Include extension so CSET's filename handling strips `.png` rather
                # than splitting on `.` in parent directories/usernames.
                plot_basename = plot_cube.name() + suffix + ".png"
                plotdir.mkdir(parents=True, exist_ok=True)
                cset_plot.spatial_pcolormesh_plot(
                    plot_cube,
                    str(plotdir / plot_basename),
                    "time",
                )
finally:
    if plot:
        cset_plot.get_recipe_metadata = _orig_get_recipe_metadata
        cset_plot._append_to_plot_index = _orig_append_to_plot_index
        cset_plot._make_plot_html_page = _orig_make_plot_html_page
        cset_plot._set_postage_stamp_title = _orig_set_postage_stamp_title
        cset_plot.colorbar_map_levels = _orig_colorbar_map_levels
        # Remove any sidecars if they already existed in the working directory.
        Path("meta.json").unlink(missing_ok=True)
        Path("index.html").unlink(missing_ok=True)
