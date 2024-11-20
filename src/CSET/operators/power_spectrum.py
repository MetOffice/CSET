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
    # Perform 2D Fourier transform
    cube_fft = fftshift(fft2(cube.data))

    # Calculate power spectrum
    power_spectrum = np.abs(cube_fft) ** 2

    """Calculate the radial average of the power spectrum to achieve a 1D lineplot
    and not a heatmap. We chose radial average to avoid a directional 1D power spectrum.
    """
    y, x = np.indices(power_spectrum.shape)
    center = np.array([x.max() / 2, y.max() / 2])
    r = np.hypot(x - center[0], y - center[1])

    # Sort the radii and power spectrum
    ind = np.argsort(r.flat)
    r_sorted = r.flat[ind]
    power_spectrum_sorted = power_spectrum.flat[ind]

    # Calculate the radial average
    r_bin_edges = np.arange(0, r.max() + 1, 1)
    r_bin_centers = (r_bin_edges[:-1] + r_bin_edges[1:]) / 2
    radial_mean = np.zeros(len(r_bin_centers))

    for i in range(len(r_bin_centers)):
        mask = (r_sorted >= r_bin_edges[i]) & (r_sorted < r_bin_edges[i + 1])
        radial_mean[i] = power_spectrum_sorted[mask].mean()

    # Create a new 1D cube for the radial average power spectrum
    radial_average_cube = iris.cube.Cube(
        radial_mean,
        long_name="radial_average_power_spectrum",
        units="unknown",
        dim_coords_and_dims=[
            (iris.coords.DimCoord(r_bin_centers, long_name="radius", units="1"), 0)
        ],
    )

    return radial_average_cube
