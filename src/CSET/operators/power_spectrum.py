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
    cube: iris.cube.Cube | iris.cube.CubeList,
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
    # If cube is a CubeList, extract the first cube
    if isinstance(cube, iris.cube.CubeList):
        cube = cube[0]

    # Extract time coordinate and convert to datetime
    if cube.coords("time"):
        time_coord = cube.coord("time")
        time_points = time_coord.units.num2date(time_coord.points)
        time_points_set = set(time_points)
        time_constraints = iris.Constraint(
            time=lambda cell: cell.point in time_points_set
        )
        cube_time_slice = cube.extract(time_constraints)

        if cube_time_slice is None:
            raise ValueError(f"No cube found for time points {time_points}")
        else:
            cube = cube_time_slice

    # Regional domains:
    # Calculate power spectra using discrete cosine transform

    # Cube used in DCT_ps must be 3D. Reshape cubes with 1 time entry,
    # to include a time dimension
    if cube.ndim == 2:
        cube_3d = cube.data[np.newaxis, :, :]
    elif cube.ndim == 3:
        cube_3d = cube.data
    else:
        raise ValueError("Cube dimensions unsuitable for power spectra code")

    # Calculate spectra
    #    ps_cube = DCT_ps(cube_3d)
    ps_array = DCT_ps(cube_3d)

    ps_cube = icube.Cube(
        ps_array,
        long_name="power_spectra",
    )

    #    ps_cube.__dict__.update(cube.__dict__)
    # Copy model_name attribute (might need oethers at some point)
    ps_cube.attributes["model_name"] = cube.attributes.get("model_name")

    # Create a frequency/wavelength array for coordinate
    ps_len = ps_cube.data.shape[1]
    freqs = np.arange(1, ps_len + 1)
    freq_coord = iris.coords.DimCoord(freqs, long_name="frequency", units="1")

    # Convert datetime to numeric time using original units
    numeric_time = time_coord.units.date2num(time_points)
    # Create a new DimCoord with numeric time
    new_time_coord = iris.coords.DimCoord(
        numeric_time, standard_name="time", units=time_coord.units
    )

    # Add time and frequency coordinate to spectra cube.
    ps_cube.add_dim_coord(new_time_coord.copy(), 0)
    ps_cube.add_dim_coord(freq_coord.copy(), 1)

    return ps_cube


def DCT_ps(y_3d):
    """Calculate power spectra for regional domains.

    # Regional domains:
    # Calculate power spectra over limited are domain using Discrete Cosine Transform (DCT)
    # as described in Denis et al 2002 [Denis_etal_2002]_.

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
    alpha_matrix = create_alpha_matrix(Ny, Nx)

    # Prepare output array
    ps_array = np.zeros((Nt, Nmin))

    # Loop over time to get spectrum for each time.
    for t in range(Nt):
        y_2d = y_3d[t]

        # Apply 2D DCT to transform y_3d[t] from physical space to spectral space.
        # fkk is a 2D array of DCT coefficients, representing the amplitudes of
        # cosine basis functions at different spatial frequencies.

        # fkk = fft.dctn(y_2d)
        # normalise spectrum
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


#    # Create cube
#    ps_cube = icube.Cube(
#        ps_array,
#        long_name="power_spectra",
#    )
#
#    return ps_cube


def create_alpha_matrix(Ny, Nx):
    """Construct an array of 2D wavenumbers from 2D wavenumber pair.

    Each pair is associated with a single-scale parameter. alpha_matrix is normalisation of
    2D wavenumber axes, transforming the spectral domain into an elliptic coordinate system.
    """
    # Create x_indices: each row is [1, 2, ..., Nx]
    x_indices = np.tile(np.arange(1, Nx + 1), (Ny, 1))

    # Create y_indices: each column is [1, 2, ..., Ny]
    y_indices = np.tile(np.arange(1, Ny + 1).reshape(Ny, 1), (1, Nx))

    # Compute alpha_matrix
    alpha_matrix = np.sqrt((x_indices**2) / Nx**2 + (y_indices**2) / Ny**2)

    return alpha_matrix
