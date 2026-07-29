"""
Some code

MAINTAINER: james.warner@metoffice.gov.uk / jwarner8
"""


import iris

def _coord_is_effectively_scalar(coord):
    """True if coordinate is scalar or all points have the same value."""
    points = np.asarray(coord.points)

    if points.size <= 1:
        return True

    return np.all(points == points.flat[0])


def _fix_analysis_forecasttime(cubes: iris.cube.CubeList):

    """
    TODO - in progress
    """

    # Partition out forecast and analysis cubes based on forecast_period.
    analysis_cubes = iris.cube.CubeList()
    forecast_cubes = iris.cube.CubeList()

    for cube in cubes:
        fp = cube.coord("forecast_period")

        if fp.points.max() == 0:
            analysis_cubes.append(cube)
        else:
            forecast_cubes.append(cube)

    if len(analysis_cubes) > 1:
        raise ValueError
    if len(forecast_cubes) > 1:
        print(forecast_cubes)
        raise ValueError
    if len(analysis_cubes) == 0:
        return cubes #i.e. no reanalysis so ignore this function

    
    analysis_cube = analysis_cubes[0]
    forecast_cube = forecast_cubes[0]

    # Analysis cube will think it has multiple realizations cause it duplicates
    analysis_cube = analysis_cube.extract(iris.Constraint(realization = analysis_cube.coord('realization').points[0]))

    # Get forecast_reference_time and period information
    frt_coord = forecast_cube.coord("forecast_reference_time")

    fc_period_coord = forecast_cube.coord("forecast_period")
    fc_periods = fc_period_coord.points
    fc_length = fc_periods[-1]

    # Work out minimum, maximum valid times in analysis
    an_min = analysis_cube.coord("time").units.num2date(analysis_cube.coord("time").points[0])
    an_max = analysis_cube.coord("time").units.num2date(analysis_cube.coord("time").points[-1])

    fixed_analysis_cubes = iris.cube.CubeList()

    # Iterate over all forecast reference times
    for t in frt_coord.points:
        frt = frt_coord.units.num2date(t)

        if frt < an_min or (
            frt + dt.timedelta(hours=float(fc_length))
        ) > an_max:

            raise ValueError(
                f"Analysis does not cover forecast span "
                f"{frt} -> "
                f"{frt + dt.timedelta(hours=float(fc_length))}")
            
    
        time_constraint = iris.Constraint(
        time=lambda cell: frt <= cell.point <= frt+dt.timedelta(hours=fc_length)
    )

        analysis_slice = analysis_cube.extract(time_constraint)

       # Remove old coords
        analysis_slice.remove_coord("forecast_reference_time")
        analysis_slice.remove_coord("forecast_period")


        time_coord = analysis_slice.coord("time")
        time_dim = analysis_slice.coord_dims("time")[0]

        # Forecast periods relative to this FRT.
        #
        fp_points = (
            time_coord.points - time_coord.points[0]
        )

        fp_coord = iris.coords.DimCoord(
            fp_points,
            standard_name="forecast_period",
            units='hours',
        )

        # Replace time dimension coord with forecast_period.
        #
        analysis_slice.remove_coord("time")
        analysis_slice.add_dim_coord(fp_coord, time_dim)

        # Add FRT scalar coordinate.
        #
        analysis_slice.add_aux_coord(
            iris.coords.AuxCoord(
                t,
                standard_name="forecast_reference_time",
                units=frt_coord.units,
            )
        )

        fixed_analysis_cubes.append(
            analysis_slice
        )

    if len(fixed_analysis_cubes) == 1:

        cube = fixed_analysis_cubes[0]

        fp_coord = cube.coord("forecast_period")

        time_points = (
            cube.coord(
                "forecast_reference_time"
            ).points[0]
            + fp_coord.points
        )

        time_coord = iris.coords.AuxCoord(
            time_points,
            standard_name="time",
            units=frt_coord.units,
        )

        cube.add_aux_coord(
            time_coord,
            data_dims=(
                cube.coord_dims(
                    "forecast_period"
                )[0],
            ),
        )

    else:
        # multiple FRTs
        #
        cube = fixed_analysis_cubes.merge_cube()

        fp_dim = cube.coord_dims(
            "forecast_period"
        )[0]

        frt_dim = cube.coord_dims(
            "forecast_reference_time"
        )[0]

        fp_points = cube.coord(
            "forecast_period"
        ).points

        frt_points = cube.coord(
            "forecast_reference_time"
        ).points

        time_points = (
            fp_points[:, None]
            + frt_points[None, :]
        )

        time_coord = iris.coords.AuxCoord(
            time_points,
            standard_name="time",
            units=frt_coord.units,
        )

        cube.add_aux_coord(
            time_coord,
            data_dims=(fp_dim, frt_dim),
        )

        fixed_analysis_cubes = iris.cube.CubeList()
        fixed_analysis_cubes.append(cube)

    return iris.cube.CubeList([cube, forecast_cube])
