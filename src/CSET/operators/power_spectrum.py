# © Crown copyright, Met Office (2022-2024) and CSET contributors.
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

"""Operator to calculate power spectrum from a 2D cube or CubeList."""

import logging

import iris
import numpy as np
from scipy.fft import fft2, fftshift


def calculate_power_spectrum(
    cube: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube:
    r"""Power spectrum is calculated.

    Arguments
    ---------
    cube: iris.cube.Cube | iris.cube.CubeList
        Cube(s) to filter

    Returns
    -------
    iris.cube.Cube

    Raises
    ------
    ValueError
        If the constraint doesn't produce a single cube.
    """
    # Check if the cube has at least 2 dimensions
    if cube.ndim < 2:
        logging.debug("Cube must have at least 2 dimensions", cube.ndim, cube.shape)
        raise ValueError("Cube must have at least 2 dimensions")

    # Handle 3D cube (time,x,y)
    if cube.ndim == 3:
        logging.info("Calculating power spectrum for 3D cube")
        power_spectra = []
        for t in range(cube.shape[0]):
            # Access the last two dimensions (x, y) for each time slice
            data_slice = cube[t].data
            cube_fft = fftshift(fft2(data_slice))
            power_spectrum = np.abs(cube_fft) ** 2
            power_spectra.append(power_spectrum)

        # Stack the power spectra along the time dimension
        power_spectra = np.stack(power_spectra)
        logging.info("Power spectrum calculated for 3D cube", power_spectra.shape)
    else:
        # Handle 2D cube (x, y)
        logging.info("Calculating power spectrum for 2D cube")
        cube_fft = fftshift(fft2(cube.data))
        power_spectrum = np.abs(cube_fft) ** 2
        power_spectra = power_spectrum[np.newaxis, ...]

    # Calculate the radial average of the power spectrum for each time slice
    radial_means = []
    for t in range(power_spectra.shape[0]):
        power_spectrum = power_spectra[t]
        y, x = np.indices(power_spectrum.shape)
        center = np.array([x.max() / 2, y.max() / 2])
        r = np.hypot(x - center[0], y - center[1])

        # Create bins for the radial distances
        r_bin_edges = np.arange(0, r.max() + 1, 1)
        r_bin_centers = (r_bin_edges[:-1] + r_bin_edges[1:]) / 2

        # Digitize the radial distances to find the bin index for each point
        r_bin_indices = np.digitize(r.flat, r_bin_edges) - 1

        # Calculate the radial average using np.bincount
        radial_sum = np.bincount(r_bin_indices, weights=power_spectrum.flat)
        radial_count = np.bincount(r_bin_indices)
        radial_mean = radial_sum / radial_count

        radial_means.append(radial_mean)

    # Stack the radial averages along the time dimension
    radial_means = np.stack(radial_means)

    # Create a new 2D cube for the radial average power spectrum
    radial_average_cube = iris.cube.Cube(
        radial_means,
        long_name="radial_average_power_spectrum",
        units="unknown",
        dim_coords_and_dims=[
            (cube.coord("time"), 0),
            (iris.coords.DimCoord(r_bin_centers, long_name="radius", units="1"), 1),
        ],
    )
    logging.info("Radial average power spectrum calculated", radial_average_cube.shape)
    return radial_average_cube
