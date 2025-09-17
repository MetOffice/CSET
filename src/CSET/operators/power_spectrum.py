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
import iris.cube as icube
import numpy as np
import scipy.fft as fft


def calculate_power_spectrum(
    #    cube: iris.cube.Cube | iris.cube.CubeList,
    # ) -> iris.cube.Cube:
    cube: iris.cube.Cube,
    filename: str = None,
    **kwargs,
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
    # Extract the time coordinate of cube for use later

    time_coord = cube[0].coord("time")

    # Regional domains:
    # Calculate power spectra using discrete cosine transform

    ps = DCT_ps(cube[0].data)

    # Reshape data to (time, frequency)
    ps_cube = ps[np.newaxis, :]

    # Create a frequency/wavelength array for

    ps_len = ps.data.shape[0]
    freqs = np.arange(1, ps_len + 1)
    freq_coord = iris.coords.DimCoord(freqs, long_name="frequency", units="m2/s2")

    # Add time and frequency coordinate to cube.

    ps_cube.add_dim_coord(time_coord.copy(), 0)
    ps_cube.add_dim_coord(freq_coord.copy(), 1)

    return ps_cube


def DCT_ps(y_2d):
    """Calculate power spectra for regional domains.

    # Regional domains:
    # Calculate power spectra over linited are domain using Discrete Cosine Transform (DCT)
    # as described in Denis et al 2002 [Denis_etal_2002].

    References
    ----------
    .. [Denis_etal_2002] Bertrand Denis, Jean Côté and René Laprise (2002)
        "Spectral Decomposition of Two-Dimensional Atmospheric Fields on
        Limited-Area Domains Using the Discrete Cosine Transform (DCT)"
        Monthly Weather Review, Vol. 130, 1812-1828
        doi: https://doi.org/10.1175/1520-0493(2002)130<1812:SDOTDA>2.0.CO;2
    """
    # Find dimensions of array and create normalised 2D wavenumber
    Ny, Nx = y_2d.shape

    alpha_matrix = create_alpha_matrix(Ny, Nx)

    # Apply 2D DCT to transform y_2d from physical space to spectral space.
    # fkk is a 2D array of DCT coefficients, representing the amplitudes of cosine basis functions
    # at different spatial frequencies.

    fkk = fft.dctn(y_2d)

    # Normalise fkk
    fkk = fkk / np.sqrt(Ny * Nx)

    # do variance of spectral coeff
    sigma_2 = fkk**2 / Nx / Ny

    # Max coefficient
    Nmin = min(Nx - 1, Ny - 1)

    ps = np.zeros(Nmin)
    # Group ellipses of alphas into the same wavenumber k/Nmin
    for k in range(1, Nmin + 1):
        alpha = k / Nmin
        alpha_p1 = (k + 1) / Nmin
        # Sum up elements matching k
        mask_k = np.where((alpha_matrix >= alpha) & (alpha_matrix < alpha_p1))
        ps[k - 1] = np.sum(sigma_2[mask_k])

        # Create the cube
        ps_cube = icube.Cube(
            ps,
            long_name="power_spectra",
        )
    #            dim_coords_and_dims=[(wavelength, 0)]

    # N=len(ps_len)
    # k=np.arange(1,N+1)

    return ps_cube


def create_alpha_matrix(Ny, Nx):
    """Construct an array of 2D wavenumbers from 2D wavenumber pair.

    Each pair is associated with a single-scale parameter. alpha_matrix is normalisation of
    2D wavenumber axes, transforming the spectral domain into an elliptic coordinate system.
    """
    # Claudio's original code
    #    for n in range(1, Ny):
    #        I = np.append(I, np.arange(Nx) + 1)
    #
    #    I.resize(Ny, Nx)
    #
    #    J = np.arange(Ny) + 1
    #    for n in range(1, Nx):
    #        J = np.append(J, np.arange(Ny) + 1)
    #
    #    J.resize(Nx, Ny)
    #    J = np.transpose(J)
    #
    #    alpha_matrix_old = np.sqrt(I * I / Nx**2 + J * J / Ny**2)

    # optimise using Copilot

    # Create x_indices: each row is [1, 2, ..., Nx]
    x_indices = np.tile(np.arange(1, Nx + 1), (Ny, 1))

    # Create y_indices: each column is [1, 2, ..., Ny]
    y_indices = np.tile(np.arange(1, Ny + 1).reshape(Ny, 1), (1, Nx))

    # Compute alpha_matrix
    alpha_matrix = np.sqrt((x_indices**2) / Nx**2 + (y_indices**2) / Ny**2)

    #    print('Alpha ',np.max(alpha_matrix_old - alpha_matrix))

    return alpha_matrix
