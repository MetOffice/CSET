# Copyright 2024 Met Office and contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Operators to extract a cross section given a tuple of xy coords to start/finish."""

from math import atan2, cos, radians, sin, sqrt

import numpy as np

# Usual names for spatial coordinates.
# TODO can we determine grid coord names in a more intelligent way?
X_COORD_NAMES = ["longitude", "grid_longitude", "projection_x_coordinate", "x"]
Y_COORD_NAMES = ["latitude", "grid_latitude", "projection_y_coordinate", "y"]


def calc_dist(coord_1, coord_2):
    """Haversine distance in meters."""
    # Approximate radius of earth in km
    R = 6378.0

    # extract coordinates and convert to radians
    lat1 = radians(coord_1[0])
    lon1 = radians(coord_1[1])
    lat2 = radians(coord_2[0])
    lon2 = radians(coord_2[1])

    # Find out delta latitude, longitude
    dlon = lon2 - lon1
    dlat = lat2 - lat1

    # Compute distance
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance * 1000


def calc_crosssection(cube, startxy, endxy, coord="latitude"):
    """Compute cross section."""
    # Compute minimum gap between coords - in case variable res, default to minimum.
    xmin = np.min(
        cube.coord("longitude").points[1:] - cube.coord("longitude").points[:-1]
    )
    ymin = np.min(
        cube.coord("latitude").points[1:] - cube.coord("latitude").points[:-1]
    )

    # For scenarios where coord is at 90 degree (no latitude/longitude change).
    if xmin == 0:
        latslice_only = True
        deltamin = ymin
    else:
        latslice_only = False
        deltamin = np.min([xmin, ymin])

    if ymin == 0:
        lonslice_only = True
        deltamin = xmin
    else:
        lonslice_only = False
        deltamin = np.min([xmin, ymin])

    # Compute vector distance between start and end points in degrees.
    dist_deg = np.sqrt(((startxy[0] - endxy[0]) ** 2) + ((startxy[1] - endxy[1]) ** 2))

    # Compute number of steps to interpolate
    nsteps = dist_deg / deltamin

    for i in range(0, int(nsteps) + 1):
        print(i)

        print(latslice_only, lonslice_only)
        # Put in a tuple - faster, and pass directly to interpolator.


#        cube_slice = cube.interpolate(
#            [
#                ("latitude", startxy[0] + (step * i)),
#                ("longitude", startxy[1] + (step * i)),
#            ],
#            iris.analysis.Linear(),
#        )


#    if coord == 'distance':
#        # one step at end potentially at end and add to cube after merge.
#        dist = calc_dist((start_xy[0],start_xy[1]), (start_xy[0]+(step*i),start_xy[1]+(step*i)))
#        dist_coord = iris.coords.AuxCoord(dist, long_name='distance', units='m')

#        cube_slice.add_aux_coord(dist_coord)
#        cube_slice = iris.util.new_axis(cube_slice,scalar_coord='distance')
#        cube_slice.remove_coord('latitude')
#        cube_slice.remove_coord('longitude')

#        interpolated_cubes.append(cube_slice)


#    print(nsteps)

#    quit()

#    # Check if case of cross section across latitude with no change in longitude.
#    if xmin != 0:
#        xpnts = np.arange(startxy[1],endxy[1],ymin)
#    else:
#        xpnts = startxy[1]

#    # Check if case of cross section across longitude with no change in latitude.
#    if ymin != 0:
#        ypnts = np.arange(startxy[0],endxy[0],ymin)
#    else:
#        ypnts = startxy[0]

#    print(xpnts.shape)
#    print(ypnts.shape)
#    quit()
#
#   # interpolated_cubes = iris.cube.CubeList()
#    cube_slice = cube.interpolate([('latitude',ypnts),('longitude',xpnts)], iris.analysis.Linear())

##    print(ypnts)

#    quit()

#    # this could go to infinite
#    step = np.min([np.min(cube.coord('latitude').points[1:]-cube.coord('latitude').points[:-1]),
#                   np.min(cube.coord('longitude').points[1:]-cube.coord('longitude').points[:-1])])


#    dist_deg = np.sqrt(((start_xy[0]-end_xy[0])**2)+((start_xy[1]-end_xy[1])**2))

#


#        #


#        print(cube_slice)
#        print(cube_slice.shape)
#        print(cube_slice.coord('distance'))

#    print(iris.util.describe_diff(interpolated_cubes[0],interpolated_cubes[1]))
#    print(interpolated_cubes.merge())
#    print(interpolated_cubes.concatenate()[0])
#    print(interpolated_cubes.concatenate()[0].coord('distance'))


# calc_crosssection(cube=iris.load_cube('/scratch/jawarner/tmp_2304/20210422T0600Z_Regn1_resn_1_RA2T_pz024.pp','air_temperature')[4,10,:,:],
#                  startxy=(-2,35),
#                  endxy=(7,38))
