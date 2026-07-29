"""
Code that restructures reanalysis data to give it an effective forecast_period, so it can
be directly compared to model forecasts in CSET.
The code base currently supports UM and ERA5, and does not perform any additional metadata
correction beyond time axis and removing some surplus coords/attributes.

Please see README for futher information on how to run the script.
"""

import iris
import iris.cube

iris.FUTURE.date_microseconds = True
iris.FUTURE.save_split_attrs = True
import argparse
from datetime import datetime, timedelta


def _create_forecasts(reanalysis, forecast_initialisations, forecastlength, outpath):
    """
    TODO - in progress
    """
    for forecast in forecast_initialisations:
        print(f"Working on forecast initialisation {forecast} out to {forecastlength}H")

        start = forecast
        end = forecast + timedelta(hours=forecastlength)

        cutouts = iris.cube.CubeList()

        for cube in reanalysis:
            print(f"{cube.name()}...")

            # Work out minimum, maximum valid times in analysis
            an_min = cube.coord("time").units.num2date(cube.coord("time").points[0])
            an_max = cube.coord("time").units.num2date(cube.coord("time").points[-1])

            if start < an_min or end > an_max:
                print("WARNING!! SOMEthING...")
            else:
                time_constraint = iris.Constraint(
                    time=lambda cell: start <= cell.point <= end
                )

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

                time_coord = cube_slice.coord("time")
                time_dim = cube_slice.coord_dims("time")[0]

                # Forecast periods relative to this FRT.
                fp_points = time_coord.points - time_coord.points[0]

                units_str = str(time_coord.units)

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

                fp_coord = iris.coords.DimCoord(
                    fp_points,
                    standard_name="forecast_period",
                    units=fp_units,
                )

                cube_slice.remove_coord("time")
                cube_slice.add_dim_coord(fp_coord, time_dim)

                cube_slice.add_aux_coord(
                    iris.coords.AuxCoord(
                        time_coord.units.date2num(start),
                        standard_name="forecast_reference_time",
                        units=time_coord.units,
                    )
                )

                time_points = (
                    cube_slice.coord("forecast_reference_time").points[0]
                    + fp_coord.points
                )

                new_time_coord = iris.coords.AuxCoord(
                    time_points,
                    standard_name="time",
                    units=time_coord.units,
                )

                cube_slice.add_aux_coord(
                    new_time_coord,
                    data_dims=(cube_slice.coord_dims("forecast_period")[0],),
                )

                print(cube_slice)
                quit()

                cutouts.append(cube_slice)
                print(f"{cube.name()}...done.")

        print(f"Saving {outpath + '/reanalysis_' + start.strftime('%Y%m%dT%H%MZ')}.nc")
        iris.save(
            cutouts, outpath + "/reanalysis_" + start.strftime("%Y%m%dT%H%MZ") + ".nc"
        )


def _identify_number_of_cycles_required(
    cyclestart: str, cycleend: str, cyclefreq: str
) -> list:
    """Generate forecast initialisation datetimes between two cycle bounds.

    Parameters
    ----------
    cyclestart : str
        First forecast cycle in YYYYMMDDTHHMMZ format.
    cycleend : str
        Last forecast cycle in YYYYMMDDTHHMMZ format.
    cyclefreq : int
        Frequency between forecast cycles in hours.

    Returns
    -------
    forecast_initialisations: list
        Forecast initialisation datetimes from cyclestart to cycleend,
        inclusive, separated by cyclefreq hours.
    """
    # Identify the start and end times, and create datetime objects for these
    start_dt = datetime.strptime(cyclestart, "%Y%m%dT%H%MZ")
    end_dt = datetime.strptime(cycleend, "%Y%m%dT%H%MZ")

    # To store initialisation times
    forecast_initialisations = []
    current = start_dt

    # Iterate over all initiations within the bounds, using the cyclefreq to determine interval.
    while current <= end_dt:
        forecast_initialisations.append(current)
        current += timedelta(hours=cyclefreq)

    return forecast_initialisations


def main() -> None:
    """Generate forecast-like datasets from reanalysis data.

    Parse command-line arguments, create forecast initialisation times,
    process the input reanalysis data, and write the resulting forecast
    files to disk.
    """
    parser = argparse.ArgumentParser(description="Process forecast data.")

    parser.add_argument("--filepath", required=True, help="Path to file(s)")
    parser.add_argument(
        "--cyclestart", type=str, required=True, help="First forecast initiation/cycle"
    )
    parser.add_argument(
        "--cycleend", type=str, required=True, help="Final forecast initiation/cycle"
    )
    parser.add_argument(
        "--cyclefreq",
        type=int,
        required=True,
        help="Time between forecast initiationss/cycles",
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
    cyclefreq = args.cyclefreq
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
