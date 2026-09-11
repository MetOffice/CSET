
import logging

import iris
import iris.analysis.calculus
import numpy as np
from iris.cube import Cube, CubeList

logger = logging.getLogger(__name__)


def _extract_common_time_points_multiple_cubes(cubes:  CubeList | Cube) -> CubeList | Cube:
    """Equalise time points across all cubes."""

    if isinstance(cubes,Cube) or len(cubes) < 2:
        return cubes
    if cubes[0].coords("forecast_reference_time"):
        return _extract_common_time_points_multiple_cubes_with_frt(cubes)
    else:
        return _extract_common_time_points_multiple_cubes_no_frt(cubes)

def _extract_common_time_points(base: Cube, other: Cube) -> tuple[Cube, Cube]:
    """Extract common time points from cubes to allow comparison."""
    # Get the name of the first non-scalar time coordinate.

    if base.coords("forecast_reference_time") and np.size(base.coords("forecast_reference_time"))>1:
        return _extract_common_time_points_with_frt(base, other)
    else:
        return _extract_common_time_points_no_frt(base, other)


def _extract_common_time_points_multiple_cubes_with_frt(cubes: CubeList) -> CubeList:


    # Check all cubes have identical FRTs.
    reference_frts = cubes[0].coord("forecast_reference_time").points

    for cube in cubes[1:]:
        cube_frts = cube.coord("forecast_reference_time").points

        if not np.array_equal(reference_frts, cube_frts):
            raise ValueError(
                "Cubes do not share the same "
                "forecast_reference_time values."
            )

    # Start from the first cube's forecast periods.
    shared_periods = set(
        cubes[0].coord("forecast_period").points
    )

    # Find intersection across all cubes.
    for cube in cubes[1:]:
        shared_periods &= set(
            cube.coord("forecast_period").points
        )

    if not shared_periods:
        raise ValueError("No common forecast periods found.")

    logger.debug(
        "Common forecast periods: %s",
        sorted(shared_periods),
    )

    constraint = iris.Constraint(
        forecast_period=lambda cell, shared_periods=shared_periods: (
                cell.point in shared_periods
        )
    )

    output = CubeList()

    for cube in cubes:
        extracted = cube.extract(constraint)

        if extracted is None:
            raise ValueError(
                f"No common forecast periods remain for {cube.name()}"
            )

        output.append(extracted)

    return output

def _extract_common_time_points_multiple_cubes_no_frt(cubes: CubeList) -> CubeList:
    base = cubes[0]
    time_coord = next(
        (
            coord.name()
            for coord in base.coords()
            if coord.shape > (1,) and coord.name() in ("time", "hour")
        ),
        None,
    )
    if not time_coord:
        logger.debug("No time coord, skipping equalisation.")
        return cubes

    base_time_coord = base.coord(time_coord)
    shared_times = set(_get_time_points(base_time_coord))
    logger.debug("Shared times: %s", shared_times)

    for other in cubes[1:]:
        other_time_coord = other.coord(time_coord)
        logger.debug("Base: %s\nOther: %s", base_time_coord, other_time_coord)
        shared_times &= set(_get_time_points(other_time_coord))
        logger.debug("Shared times: %s", shared_times)

    if not shared_times:
        raise ValueError("No common time points found!")

    time_constraint = iris.Constraint(
        coord_values={
            time_coord: lambda cell, shared_times=shared_times: cell.point in shared_times
        }
    )
    return cubes.extract(time_constraint)

def _extract_common_time_points_no_frt(base: Cube, other: Cube) -> tuple[Cube, Cube]:
    time_coord = next(
        (
            coord.name()
            for coord in filter(
            lambda coord: coord.shape > (1,) and coord.name() in ["time", "hour"],
            base.coords(),
        )
        ),
        None,
    )
    if not time_coord:
        logger.debug("No time coord, skipping equalisation.")
        return base, other
    base_time_coord = base.coord(time_coord)
    other_time_coord = other.coord(time_coord)
    logger.debug("Base: %s\nOther: %s", base_time_coord, other_time_coord)

    base_times = _get_time_points(base_time_coord)
    other_times = _get_time_points(other_time_coord)

    shared_times = set.intersection(set(base_times), set(other_times))

    logger.debug("Shared times: %s", shared_times)
    time_constraint = iris.Constraint(
        coord_values={
            time_coord: lambda cell, shared_times=shared_times: (
                    cell.point in shared_times
            )
        }
    )

    # Extract points matching the shared times.
    base = base.extract(time_constraint)
    other = other.extract(time_constraint)
    if base is None or other is None:
        raise ValueError("No common time points found!")
    return base, other

def _get_time_points(coord):
    """Comparable time points for a coord. 'hour' uses raw points since
    it has non-absolute units; iris auto-converts other time coords to
    datetimes for comparison, so match that here."""
    if coord.name() == "hour":
        return coord.points
    return coord.units.num2date(coord.points)


def _extract_common_time_points_with_frt(base: Cube,other: Cube) -> tuple[Cube, Cube]:
    """Equalise time points across all cubes."""

    # Check all cubes have identical FRTs.
    reference_frts = base.coord("forecast_reference_time").points
    cube_frts = other.coord("forecast_reference_time").points

    if not np.array_equal(reference_frts, cube_frts):
        raise ValueError(
            "Cubes do not share the same "
            "forecast_reference_time values."
        )

    constraint = _make_shared_period_constraint(base,other)

    base = base.extract(constraint)
    other = other.extract(constraint)

    return base,other


def _make_shared_period_constraint(base, other) -> iris.Constraint:
    # Start from the first cube's forecast periods.
    shared_periods = set(
        base.coord("forecast_period").points
    )

    # Find intersection across all cubes.

    shared_periods &= set(
        other.coord("forecast_period").points
    )

    if not shared_periods:
        raise ValueError("No common forecast periods found.")

    logger.debug(
        "Common forecast periods: %s",
        sorted(shared_periods),
    )

    return iris.Constraint(
        forecast_period=lambda cell, shared_periods=shared_periods: (
                cell.point in shared_periods
        )
    )
