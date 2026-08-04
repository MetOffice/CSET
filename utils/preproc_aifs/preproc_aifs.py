"""do something"""

from collections import defaultdict

import iris
import numpy as np
from iris.coords import DimCoord
from iris.cube import CubeList
import os

def combine_ensemble_cubes(cubes):
    """
    Convert control and perturbed ensemble cubes into a common
    realization dimension and concatenate into a single cube per variable.
    """

    processed = CubeList()

    for cube in cubes:

        cube = cube.copy()

        # Remove attributes that prevent concatenation
        cube.attributes.pop("history", None)

        if cube.coords("pressure_level"):
            pressure_coord = cube.coord("pressure_level")

            if not isinstance(pressure_coord, DimCoord):

                pressure_dim = cube.coord_dims(pressure_coord)[0]

                # Sort pressure values
                order = np.argsort(pressure_coord.points)
                sorted_points = pressure_coord.points[order]

                # Reorder data to match
                cube.data = np.take(cube.core_data(), order, axis=pressure_dim)

                # Replace aux coord with dim coord
                cube.remove_coord("pressure_level")

                cube.add_dim_coord(
                    DimCoord(
                        sorted_points,
                        long_name=pressure_coord.long_name,
                        standard_name=pressure_coord.standard_name,
                        var_name=pressure_coord.var_name,
                        units=pressure_coord.units,
                        attributes=pressure_coord.attributes,
                    ),
                    pressure_dim,
                )


        # Perturbed members
        if cube.coords("ensemble_member"):

            ensemble_coord = cube.coord("ensemble_member")

            cube.remove_coord("ensemble_member")

            realization_coord = DimCoord(
                np.arange(1, 51),
                standard_name="realization",
                units="1",
            )

            # ensemble member dimension is dimension 1
            cube.add_dim_coord(realization_coord, 1)

        # Control member
        else:

            # Add a new dimension of length 1
            cube = iris.util.new_axis(cube)

            realization_coord = DimCoord(
                [0],
                standard_name="realization",
                units="1",
            )

            # new_axis inserts the dimension at position 0
            cube.add_dim_coord(realization_coord, 0)

            # Always move realization after time
            order = list(range(cube.ndim))
            order[0], order[1] = order[1], order[0]
            cube.transpose(order)

        processed.append(cube)

    processed = processed.concatenate()
    print(processed[0])
    quit()

    # Concatenate works, i.e. below. Now need to fix metadata (names, ensure time descriptive with forecast_ref, forecast_period etc.)

# air_pressure_at_mean_sea_level / (Pa) (time: 2; realization: 51; latitude: 721; longitude: 1440)
#     Dimension coordinates:
#         time                               x               -             -               -
#         realization                        -               x             -               -
#         latitude                           -               -             x               -
#         longitude                          -               -             -               x
#     Attributes:
#         Conventions                   'CF-1.6'

# 0: 2 metre dewpoint temperature / (K)  (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 1: Runoff water equivalent (surface plus subsurface) / (kg m**-2) (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 2: Skin temperature / (K)              (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 3: Snowfall water equivalent / (kg m**-2) (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 4: Surface long-wave (thermal) radiation downwards / (J m**-2) (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 5: Total Cloud Cover / (%)             (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 6: Total Precipitation / (kg m**-2)    (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 7: Total column water / (kg m**-2)     (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 8: air_pressure_at_mean_sea_level / (Pa) (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 9: air_temperature / (K)               (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 10: air_temperature / (K)               (time: 1; realization: 51; pressure_level: 13; latitude: 721; longitude: 1440)
# 11: eastward_wind / (m s**-1)           (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 12: eastward_wind / (m s**-1)           (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 13: eastward_wind / (m s**-1)           (time: 1; realization: 51; pressure_level: 13; latitude: 721; longitude: 1440)
# 14: geopotential / (m**2 s**-2)         (time: 1; realization: 51; pressure_level: 13; latitude: 721; longitude: 1440)
# 15: lagrangian_tendency_of_air_pressure / (Pa s**-1) (time: 1; realization: 51; pressure_level: 13; latitude: 721; longitude: 1440)
# 16: northward_wind / (m s**-1)          (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 17: northward_wind / (m s**-1)          (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 18: northward_wind / (m s**-1)          (time: 1; realization: 51; pressure_level: 13; latitude: 721; longitude: 1440)
# 19: specific_humidity / (kg kg**-1)     (time: 1; realization: 51; pressure_level: 13; latitude: 721; longitude: 1440)
# 20: surface_air_pressure / (Pa)         (time: 1; realization: 51; latitude: 721; longitude: 1440)
# 21: surface_downwelling_shortwave_flux_in_air / (J m**-2) (time: 1; realization: 51; latitude: 721; longitude: 1440)
 
    # Group by variable name
    grouped = defaultdict(CubeList)

    for cube in processed:
        grouped[cube.name()].append(cube)

    # Concatenate control + perturbed members
    result = CubeList()

    for cubelist in grouped.values():
        result.append(cubelist.concatenate_cube())

    return result


orig = iris.load(os.environ['DATADIR']+'/CSET_testdata/aifs/test/*.nc','air_pressure_at_mean_sea_level')
#print(orig)
cubes = combine_ensemble_cubes(orig)

print(cubes)