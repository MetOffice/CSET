# © Crown copyright, Met Office (2022-2025) and CSET contributors.
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

"""Functions to support calculation of power spectra."""

import numpy as np
import scipy.fft as fft


def _DCT_ps(y_3d):
    """Calculate power spectra for regional domains.

    Parameters
    ----------
    y_3d: 3D array
        3 dimensional array to calculate spectrum for.
        (2D field data with 3rd dimension of time)

    Returns: ps_array
        Array of power spectra values calculated for input field (for each time)

    Method for regional domains:
    Calculate power spectra over limited area domain using Discrete Cosine Transform (DCT)
    as described in Denis et al 2002 [Denis_etal_2002]_.

    References
    ----------
    .. [Denis_etal_2002] Bertrand Denis, Jean Côté and René Laprise (2002)
        "Spectral Decomposition of Two-Dimensional Atmospheric Fields on
        Limited-Area Domains Using the Discrete Cosine Transform (DCT)"
        Monthly Weather Review, Vol. 130, 1812-1828
        doi: https://doi.org/10.1175/1520-0493(2002)130<1812:SDOTDA>2.0.CO;2
    """
    Nt, Ny, Nx = y_3d.shape

    # Max coefficient
    Nmin = min(Nx - 1, Ny - 1)

    # Create alpha matrix (of wavenumbers)
    alpha_matrix = _create_alpha_matrix(Ny, Nx)

    # Prepare output array
    ps_array = np.zeros((Nt, Nmin))

    # Loop over time to get spectrum for each time.
    for t in range(Nt):
        y_2d = y_3d[t]

        # Apply 2D DCT to transform y_3d[t] from physical space to spectral space.
        # fkk is a 2D array of DCT coefficients, representing the amplitudes of
        # cosine basis functions at different spatial frequencies.

        # normalise spectrum to allow comparison between models.
        fkk = fft.dctn(y_2d, norm="ortho")

        # Normalise fkk
        fkk = fkk / np.sqrt(Ny * Nx)

        # calculate variance of spectral coefficient
        sigma_2 = fkk**2 / Nx / Ny

        # Group ellipses of alphas into the same wavenumber k/Nmin
        for k in range(1, Nmin + 1):
            alpha = k / Nmin
            alpha_p1 = (k + 1) / Nmin

            # Sum up elements matching k
            mask_k = np.where((alpha_matrix >= alpha) & (alpha_matrix < alpha_p1))
            ps_array[t, k - 1] = np.sum(sigma_2[mask_k])

    return ps_array


def _create_alpha_matrix(Ny, Nx):
    """Construct an array of 2D wavenumbers from 2D wavenumber pair.

    Parameters
    ----------
    Ny, Nx:
        Dimensions of the 2D field for which the power spectra is calculated. Used to
        create the array of 2D wavenumbers. Each Ny, Nx pair is associated with a
        single-scale parameter.

    Returns: alpha_matrix
        normalisation of 2D wavenumber axes, transforming the spectral domain into
        an elliptic coordinate system.

    """
    # Create x_indices: each row is [1, 2, ..., Nx]
    x_indices = np.tile(np.arange(1, Nx + 1), (Ny, 1))

    # Create y_indices: each column is [1, 2, ..., Ny]
    y_indices = np.tile(np.arange(1, Ny + 1).reshape(Ny, 1), (1, Nx))

    # Compute alpha_matrix
    alpha_matrix = np.sqrt((x_indices**2) / Nx**2 + (y_indices**2) / Ny**2)

    return alpha_matrix
