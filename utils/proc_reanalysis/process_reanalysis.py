"""
Code that restructures reanalysis data to give it an effective forecast_period.

As a result, reanalysis can be directly compared to model forecasts in CSET and treated as another model.
The code base currently supports UM and ERA5, and does not perform any additional metadata
correction beyond time axis and removing some surplus coords/attributes.

Please see README for further information on how to run the script.
"""

import iris
import iris.cube

iris.FUTURE.date_microseconds = True
iris.FUTURE.save_split_attrs = True
import argparse
from datetime import datetime, timedelta


def _identify_number_of_cycles_required(
    cyclestart: datetime, cycleend: datetime, cyclefreq: timedelta
) -> list:
    """Generate forecast initialisation datetimes between two cycle bounds.

    Parameters
    ----------
    cyclestart : datetime
        First forecast cycle time.
    cycleend : datetime
        Last forecast cycle time.
    cyclefreq : timedelta
        Frequency between forecast cycles in hours.

    Returns
    -------
    forecast_initialisations: list
        Forecast initialisation datetimes from start_dt to end_dt,
        inclusive, separated by cyclefreq hours.
    """
    # To store initialisation times
    forecast_initialisations = []
    current = cyclestart

    # Iterate over all initiations within the bounds, using the cyclefreq to determine interval.
    while current <= cycleend:
        forecast_initialisations.append(current)
        current += timedelta(hours=cyclefreq)

    return forecast_initialisations


def _create_forecasts(
    reanalysis: iris.cube.CubeList,
    forecast_initialisations: list,
    forecastlength: int,
    outpath: str,
) -> None:
    """Create forecast files from reanalysis data.

    For each forecast initialisation time, extract the corresponding
    analysis period from each input cube and convert it into a
    forecast-style representation. This includes generating
    forecast-period and forecast-reference-time coordinates and
    writing the resulting cubes to disk.

    Parameters
    ----------
    reanalysis: iris.cube.CubeList
        Collection of reanalysis cubes from which forecast periods
        will be extracted.
    forecast_initialisations: list
        Forecast initialisation times to process.
    forecastlength: int
        Forecast length in hours.
    outpath: str
        Directory to which the generated forecast files will be saved.

    Returns
    -------
    None
    """
    # Iterate over all forecast initialisations sequentially.
    for forecast in forecast_initialisations:
        print(f"Working on forecast initialisation {forecast} out to {forecastlength}H")

        # Work out start and end time
        start = forecast
        end = forecast + timedelta(hours=forecastlength)

        cutouts = iris.cube.CubeList()

        # For each cube (variable) loaded
        for cube in reanalysis:
            print(f"{cube.name()}...")

            # Work out minimum, maximum valid times in analysis
            an_min = cube.coord("time").units.num2date(cube.coord("time").points[0])
            an_max = cube.coord("time").units.num2date(cube.coord("time").points[-1])

            # Check reanalysis spans what we are looking for time wise, otherwise ignore
            if start < an_min or end > an_max:
                print(
                    f"Warning: Required time {start} {end} outside that found in analysis {an_min} {an_max}"
                )
            else:
                # Generate time constraint object inclusive of time bounds.
                time_constraint = iris.Constraint(
                    time=lambda cell, start=start, end=end: start <= cell.point <= end
                )

                # Extract required timeslice.
                cube_slice = cube.extract(time_constraint)

                # Remove unnecessary coords and attributes
                coords_attrs_to_remove = [
                    "forecast_period",
                    "forecast_reference_time",
                    "originating_centre",
                    "source",
                    "um_version",
                ]
                for item in coords_attrs_to_remove:
                    if cube_slice.coords(item):
                        cube_slice.remove_coord(item)
                    if item in cube_slice.attributes:
                        del cube_slice.attributes[item]

                # Get a copy of time coord, and dimension this corresponds to.
                time_coord = cube_slice.coord("time")

                # Work out units of forecast_period and adjust if necessary.
                units_str = str(time_coord.units)

                # Forecast periods relative to initialisation.
                fp_points = time_coord.points - time_coord.points[0]

                if units_str.startswith("seconds since"):
                    fp_points = fp_points / 3600.0
                    fp_units = "hours"
                elif units_str.startswith("minutes since"):
                    fp_points = fp_points / 60.0
                    fp_units = "hours"
                elif units_str.startswith("hours since"):
                    fp_units = "hours"
                else:
                    raise ValueError(f"Unhandled time units: {time_coord.units}")

                # Get copy of time coordinate
                time_coord_points = time_coord.points.copy()
                time_dim = cube_slice.coord_dims("time")[0]

                # Create forecast period dimension
                fp_coord = iris.coords.DimCoord(
                    fp_points,
                    standard_name="forecast_period",
                    units=fp_units,
                )

                # Remove time dimension temporarily, as forecast_period will be lead dimension
                cube_slice.remove_coord("time")
                cube_slice.add_dim_coord(fp_coord, time_dim)

                # Add auxiliary forecast initialisation dimension
                cube_slice.add_aux_coord(
                    iris.coords.AuxCoord(
                        time_coord.units.date2num(start),
                        standard_name="forecast_reference_time",
                        units=time_coord.units,
                    )
                )

                # Create auxiliary time dimension of valid time.
                new_time_coord = iris.coords.AuxCoord(
                    time_coord_points,
                    standard_name="time",
                    units=time_coord.units,
                )

                # Add this dimsnion to the cube, tied to the forecast_period dimension.
                cube_slice.add_aux_coord(
                    new_time_coord,
                    data_dims=(cube_slice.coord_dims("forecast_period")[0],),
                )

                # Append slice to cutout list, ready for saving.
                cutouts.append(cube_slice)
                print(f"{cube.name()}...done.")

        # Once all cubes processed, save to disk.
        if len(cutouts) > 0:
            print(
                f"Saving {outpath + '/reanalysis_' + start.strftime('%Y%m%dT%H%MZ')}.nc"
            )
            iris.save(
                cutouts,
                outpath + "/reanalysis_" + start.strftime("%Y%m%dT%H%MZ") + ".nc",
            )
        else:
            raise ValueError("No suitable cubes found for saving!")


def main() -> None:
    """Generate forecast-like datasets from reanalysis data.

    Parse command-line arguments, create forecast initialisation times,
    process the input reanalysis data, and write the resulting forecast
    files to disk.
    """
    parser = argparse.ArgumentParser(description="Process arguments.")

    parser.add_argument("--filepath", required=True, help="Path to file(s)")
    parser.add_argument(
        "--cyclestart",
        type=datetime.fromisoformat,
        required=True,
        help="First forecast initiation/cycle, in format %Y%m%dT%H%MZ",
    )
    parser.add_argument(
        "--cycleend",
        type=datetime.fromisoformat,
        required=True,
        help="Final forecast initiation/cycle, in format %Y%m%dT%H%MZ",
    )
    parser.add_argument(
        "--cyclefreq",
        type=int,
        required=True,
        help="Hours between forecast initiations/cycles",
    )
    parser.add_argument(
        "--forecastlength",
        type=int,
        required=True,
        help="Forecast length in SI units i.e. PT48H",
    )
    parser.add_argument(
        "--outpath", type=str, required=True, help="Where to write output data"
    )

    args = parser.parse_args()

    # Populate required variables
    filepath = args.filepath
    cyclestart = args.cyclestart
    cycleend = args.cycleend
    cyclefreq = timedelta(hours=args.cyclefreq)
    forecastlength = args.forecastlength
    outpath = args.outpath

    print()
    print("Starting process_reanalysis.py...")

    # Get all forecast initiations
    forecast_initialisations = _identify_number_of_cycles_required(
        cyclestart, cycleend, cyclefreq
    )

    # Load all reanalysis supplied
    print(f"Loading reanalysis from {filepath}")
    reanalysis = iris.load(filepath)
    print()
    print("Found the following cubes...")
    print(reanalysis)

    print()
    print("Creating postprocessed files...")
    _create_forecasts(reanalysis, forecast_initialisations, forecastlength, outpath)

    print("Done")


if __name__ == "__main__":
    main()
