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

"""Operators for calculating power spectra."""

import logging

import iris
import iris.coords
import iris.cube
import numpy as np
import scipy.fft as fft


def calculate_power_spectrum(cubes):
    """Wrap power spectrum code.

    This function is a wrapper that handles power spectrum 
    calculations for both single cubes and cube lists.
    
    The input cube is split up into a cube
    for each model and time and a power spectrum calculated for each before
    combining into one cube ahead of plotting.  This is done to retain the
    model_name attribute correctly for different models.

    In case of a CubeList (Mutiple models): It iterates through 
    each cube and calculates an individual power spectrum. In case of a 
    single cube (one model) it directly calculates the power spectrum.
    
    Input: Cube OR CubeList
    Output: CubeList of power spectra.
    """
    # Multi-model input (CubeList)
    if isinstance(cubes, iris.cube.CubeList):
        out = iris.cube.CubeList()
        for cube in cubes:
            model = cube.attributes.get("model_name")
            # Calculate power spectrum
            ps = _power_spectrum(cube)
            if model is not None:
                ps.attributes["model_name"] = model
            out.append(ps)
        return out

    # Single cube (one model)
    model = cubes.attributes.get("model_name")
    # Calculate power spectrum
    ps = _power_spectrum(cubes)
    if model is not None:
        ps.attributes["model_name"] = model
    return iris.cube.CubeList([ps])


def _power_spectrum(
    cube: iris.cube.Cube | iris.cube.CubeList,
) -> iris.cube.Cube | iris.cube.CubeList:
    """Calculate power spectrum for a single cube for 1 vertical level at 1 time.

    Parameters
    ----------
    cube: Cube
        Data to plot as power spectrum.
        The cubes should cover the same phenomenon i.e. all cubes contain temperature data.
        We do not support different data such as temperature and humidity in the same CubeList
        for plotting.

    Returns
    -------
    iris.cube.Cube
        The power spectrum of the data.
        To be plotted and aggregation performed after.

    Raises
    ------
    ValueError
        If the cube doesn't have the right dimensions.
    TypeError
        If the cube isn't a Cube.
    """
    # Extract time coordinate and convert to datetime
    time_coord = cube.coord("time")
    time_points = time_coord.units.num2date(time_coord.points)

    if cube.ndim == 2:
        cube_3d = cube.data[np.newaxis, :, :]
        logging.debug("Adding in new axis for a 2 dimensional cube.")
    elif cube.ndim == 3:
        cube_3d = cube.data
    else:
        raise ValueError("Cube dimensions unsuitable for power spectra code")
        raise ValueError(
            f"Cube is {cube.ndim} dimensional. Cube should be 2 or 3 dimensional."
        )

    # Calculate spectrum
    ps_array = _DCT_ps(cube_3d)

    # Ensure power spectrum output is 2D: (time, frequency)
    if ps_array.ndim == 1:
        ps_array = ps_array[np.newaxis, :]

    ps_cube = iris.cube.Cube(
        ps_array,
        long_name="power_spectral_density",
    )

    # Create a frequency/wavelength array for new coordinate
    ps_len = ps_cube.data.shape[1]
    freqs = np.arange(1, ps_len + 1)

    # Create a new DimCoord with frequency
    freq_coord = iris.coords.DimCoord(freqs, long_name="frequency", units="1")

    numeric_time = time_coord.units.date2num(time_points)
    numeric_time = np.atleast_1d(numeric_time)

    # Make time coord length match the number of spectra
    if len(numeric_time) != ps_array.shape[0]:
        numeric_time = np.repeat(numeric_time[0], ps_array.shape[0])

    new_time_coord = iris.coords.DimCoord(
        numeric_time,
        standard_name="time",
        units=time_coord.units,
    )

    ps_cube = iris.cube.Cube(
        ps_array,
        dim_coords_and_dims=[
            (new_time_coord, 0),
            (freq_coord, 1),
        ],
        long_name="power_spectral_density",
    )

    # Ensure cube has a realisation coordinate by creating and adding to cube
    realization_coord = iris.coords.AuxCoord(0, standard_name="realization", units="1")
    ps_cube.add_aux_coord(realization_coord)

    return ps_cube


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
            # Divide by number of coefficients in bin to get power spectral density insetad of power spectrum
            ps_array[t, k - 1] = np.sum(sigma_2[mask_k]) / len(mask_k[0])

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
