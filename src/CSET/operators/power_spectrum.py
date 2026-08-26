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
import iris.exceptions
import numpy as np
from scipy import fft

from CSET._common import iter_maybe

logger = logging.getLogger(__name__)


def calculate_power_spectrum(
    cubes: iris.cube.Cube | iris.cube.CubeList,
):
    """Wrap power spectrum code.

    This function is a wrapper that handles power spectrum
    calculations for both single cubes and cube lists and includes
    ensembles.

    The input cube is split into a cube for each model, time,
    forecast_reference_time and realization. A power spectrum is
    calculated for each before combining them into one cube ahead of
    plotting. Attributes (model_name, realization,
    forecast_reference_time) are retained from original cube.

    In the case of a CubeList containing multiple models, multiple
    cases or ensembles, the function iterates through each cube and
    calculates an individual power spectrum.

    In the case of a single cube, it directly calculates the power
    spectrum.

    Parameters
    ----------
    cubes : iris.cube.Cube | iris.cube.CubeList
        Field over which to calculate a power spectrum.

    Returns
    -------
    iris.cube.Cube | iris.cube.CubeList
        Power-spectrum cube, or a CubeList for multiple models.
    """
    out = iris.cube.CubeList()

    for input_cube in iter_maybe(cubes):
        model = input_cube.attributes.get("model_name")

        # Check whether data has realization and/or
        # forecast_reference_time coordinates
        has_realization = bool(input_cube.coords("realization"))
        has_frt = bool(input_cube.coords("forecast_reference_time"))

        # Build a list containing:
        # (cube_slice, realization_value, frt_value)
        #
        # Retain realization and frt values and restore to
        # power-spectrum cubes later.
        if has_realization and has_frt:
            # Both realization and forecast_reference_time coords
            members = []

            for frt_cube in input_cube.slices_over("forecast_reference_time"):
                frt = frt_cube.coord("forecast_reference_time").points[0]

                for member in frt_cube.slices_over("realization"):
                    realiz = member.coord("realization").points[0]

                    members.append((member, realiz, frt))

        elif has_realization:
            # Only realization coord
            members = []

            for member in input_cube.slices_over("realization"):
                realiz = member.coord("realization").points[0]

                members.append((member, realiz, None))

        elif has_frt:
            # Only forecast_reference_time coord.
            members = []

            for frt_cube in input_cube.slices_over("forecast_reference_time"):
                frt = frt_cube.coord("forecast_reference_time").points[0]

                members.append((frt_cube, None, frt))

        else:
            # Neither realization nor forecast_reference_time coords.
            members = [(input_cube, None, None)]

        member_power_spectra = iris.cube.CubeList()

        # Calculate the spectrum separately for every member/FRT
        # combination.
        for member, realiz, frt in members:
            # Calculate power spectrum
            ps = _power_spectrum(member)

            # Attach model name if available
            if model:
                ps.attributes["model_name"] = model

            # Add the correct realization from the parent cube.
            if realiz is not None:
                ps.add_aux_coord(
                    iris.coords.AuxCoord(
                        realiz,
                        long_name="realization",
                        units="1",
                    )
                )

                ps = iris.util.new_axis(
                    ps,
                    "realization",
                )

            # Add the forecast_reference_time from the parent cube.
            if frt is not None:
                ps.add_aux_coord(
                    iris.coords.AuxCoord(
                        frt,
                        standard_name=("forecast_reference_time"),
                        units=member.coord("forecast_reference_time").units,
                    )
                )

                # Promote to dimension coordinate.
                ps = iris.util.new_axis(
                    ps,
                    "forecast_reference_time",
                )

            member_power_spectra.append(ps)

        # If both realization and FRT vary. Concatenate in stages:
        #
        # 1. Concatenate realizations within each FRT.
        # 2. Concatenate the resulting cubes over FRT.
        if has_realization and has_frt:
            # Both realization and forecast_reference_time coords
            frt_power_spectra = iris.cube.CubeList()

            frt_values = np.unique(
                [
                    ps_cube.coord("forecast_reference_time").points[0]
                    for ps_cube in member_power_spectra
                ]
            )

            for frt in frt_values:
                cubes_for_frt = iris.cube.CubeList(
                    [
                        ps_cube
                        for ps_cube in member_power_spectra
                        if (ps_cube.coord("forecast_reference_time").points[0] == frt)
                    ]
                )

                # Within one FRT, realization is the coordinate
                # that varies.
                frt_cube = cubes_for_frt.concatenate_cube()

                frt_power_spectra.append(frt_cube)

            # If there is only one FRT, no second concatenation is
            # required.
            if len(frt_power_spectra) == 1:
                combined_cube = frt_power_spectra[0]

            else:
                # There are multiple FRTs.
                #
                # If every FRT has one time point, time and FRT vary
                # together. Make time an AuxCoord attached to the FRT
                # dimension so Iris has one concatenation dimension.
                one_time_per_frt = all(
                    frt_cube.coord("time").shape == (1,)
                    for frt_cube in frt_power_spectra
                )

                if one_time_per_frt:
                    cubes_for_frt_concat = iris.cube.CubeList()

                    for frt_cube in frt_power_spectra:
                        frt_cube = frt_cube.copy()

                        time_coord = frt_cube.coord("time").copy()

                        time_dims = frt_cube.coord_dims("time")

                        time_dim = time_dims[0]

                        # Select the only point on the time
                        # dimension. This removes that dimension but
                        # initially leaves time as a scalar coord.
                        index = [slice(None)] * frt_cube.ndim
                        index[time_dim] = 0

                        frt_cube = frt_cube[tuple(index)]

                        frt_cube.remove_coord("time")

                        frt_dims = frt_cube.coord_dims("forecast_reference_time")

                        if len(frt_dims) != 1:
                            raise ValueError(
                                "Expected "
                                "forecast_reference_time to "
                                "be a one-dimensional "
                                "coordinate."
                            )

                        frt_dim = frt_dims[0]

                        # Attach the one time point to the FRT
                        # dimension.
                        frt_cube.add_aux_coord(
                            time_coord,
                            data_dims=(frt_dim,),
                        )

                        cubes_for_frt_concat.append(frt_cube)

                    combined_cube = cubes_for_frt_concat.concatenate_cube()

                else:
                    # If all FRT cubes have the same time coordinate,
                    # only FRT varies and normal concatenation should
                    # work.
                    first_time = frt_power_spectra[0].coord("time")

                    matching_times = all(
                        frt_cube.coord("time") == first_time
                        for frt_cube in frt_power_spectra[1:]
                    )

                    if not matching_times:
                        raise ValueError(
                            "Cannot combine power spectra: "
                            "multiple forecast reference times "
                            "have different multi-point time "
                            "coordinates."
                        )

                    # Combine individual cubes into single cube.
                    combined_cube = frt_power_spectra.concatenate_cube()

        else:
            # Only one of realization or FRT varies, or neither
            # exists. In those cases only one concatenation axis is
            # required.
            # Combine individual cubes into single cube.
            if len(member_power_spectra) == 1:
                combined_cube = member_power_spectra[0]
            else:
                combined_cube = member_power_spectra.concatenate_cube()

        combined_cube = iris.util.squeeze(combined_cube)

        out.append(combined_cube)

    # Directly return cube if only one.
    if len(out) == 1:
        return out[0]

    return out


def _power_spectrum(cube: iris.cube.Cube) -> iris.cube.Cube:
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
        logger.debug("Adding in new axis for a 2 dimensional cube.")
    elif cube.ndim == 3:
        cube_3d = cube.data
    else:
        raise ValueError(
            f"Cube is {cube.ndim} dimensional. Cube should be 2 or 3 dimensional."
        )

    # Calculate spectrum
    ps_array = _DCT_ps(cube_3d)

    # Make wavenumber comparable between models with different domain sizes and
    # resolutions. Try to find appropriate spatial coordinates.
    coord_pairs = (
        ("projection_x_coordinate", "projection_y_coordinate"),
        ("grid_latitude", "grid_longitude"),
        ("latitude", "longitude"),
    )
    for x_coord_name, y_coord_name in coord_pairs:
        try:
            # Try projection coordinates first (most common for limited area models)
            x_coord = cube.coord(x_coord_name)
            y_coord = cube.coord(y_coord_name)
        except iris.exceptions.CoordinateNotFoundError:
            continue
        logger.debug(
            "Using %s and %s coordinates for grid spacing calculation.",
            x_coord_name,
            y_coord_name,
        )
        break  # Break out of loop if we found usable coords.
    else:
        # Raise error if no usable coords found.
        raise ValueError(
            "Could not find appropriate spatial coordinates. "
            "Expected one of: 'projection_x_coordinate'/'projection_y_coordinate', "
            "'grid_latitude'/'grid_longitude', or 'latitude'/'longitude'."
        )

    # Calculate grid spacing.
    dx = np.abs(np.diff(x_coord.points).mean())
    dy = np.abs(np.diff(y_coord.points).mean())
    if "latitude" in x_coord.name():
        # Convert from degrees to meters. x is lat, y is lon.
        R_earth = 6371000  # meters
        lat_mid = np.mean(x_coord.points)
        dx = dx * np.pi / 180 * R_earth * np.cos(lat_mid * np.pi / 180)
        dy = dy * np.pi / 180 * R_earth
    domain_size_km = ((dx * cube_3d.shape[2]) + (dy * cube_3d.shape[1])) / 2 / 1000

    # Convert wavenumber into physically meaningful wavenumber coordinate in
    # cycles per km rather than wavenumber per index k.
    ps_len = ps_array.shape[1]
    k_indices = np.arange(1, ps_len + 1)
    physical_wavenumbers = k_indices / domain_size_km  # cycles/km

    # Create a new DimCoord with physical wavenumber
    physical_wavenumbers_coord = iris.coords.DimCoord(
        physical_wavenumbers, long_name="physical_wavenumber", units="km-1"
    )

    # Calculate wavelength and add as auxiliary coordinate
    wavelengths = domain_size_km / k_indices  # km
    wavelength_coord = iris.coords.AuxCoord(
        wavelengths, long_name="wavelength", units="km"
    )

    # Ensure power spectrum output is 2D: (time, frequency)
    if ps_array.ndim == 1:
        ps_array = ps_array[np.newaxis, :]

    # Prepare time coordinate
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

    # Create output cube with physical coordinates
    ps_cube = iris.cube.Cube(
        ps_array,
        dim_coords_and_dims=[
            (new_time_coord, 0),
            (physical_wavenumbers_coord, 1),
        ],
        long_name="power_spectral_density",
    )

    # Add wavelength as auxiliary coordinate
    # Realization coordinate is added in _calculate_power_spectrum
    ps_cube.add_aux_coord(wavelength_coord, data_dims=1)

    return ps_cube


def _DCT_ps(y_3d):
    """Calculate power spectra for regional domains.

    Parameters
    ----------
    y_3d: 3D array
        3 dimensional array to calculate spectrum for.
        (2D field data with 3rd dimension of time)

    Returns
    -------
    ps_array:
        Array of power spectra values calculated for input field (for each time)
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

        # DCT transform and normalise spectrum to allow comparison between models.
        fkk = fft.dctn(y_2d, norm="ortho")

        # calculate variance (energy) of spectral coefficient at each wavenumber pair (k_x, k_y)
        # as the square of the DCT coefficient, normalised by the total number of grid points (Nx * Ny).
        sigma_2 = fkk**2 / Nx / Ny

        # Group ellipses of alphas into the same wavenumber k/Nmin
        for k in range(1, Nmin + 1):
            # Define the bounds of the current normalised wavenumber magnitude of bin k
            alpha = k / Nmin
            alpha_p1 = (k + 1) / Nmin

            # Sum up elements matching in bin k and divide by bin size
            mask_k = np.where((alpha_matrix >= alpha) & (alpha_matrix < alpha_p1))
            n_coeffs = len(mask_k[0])  # number of coefficients in bin k
            if n_coeffs > 0:
                ps_array[t, k - 1] = (
                    np.sum(sigma_2[mask_k]) / n_coeffs
                )  # average power in bin k
            else:
                ps_array[t, k - 1] = 0.0

    return ps_array


def _create_alpha_matrix(Ny, Nx):
    """Construct an array of 2D wavenumbers from 2D wavenumber pair.

    Parameters
    ----------
    Ny, Nx:
        Dimensions of the 2D field for which the power spectra is calculated. Used to
        create the array of 2D wavenumbers. Each Ny, Nx pair is associated with a
        single-scale parameter.

    Returns
    -------
    alpha_matrix:
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


def _coord_dimension(cube, coord_name):
    """Return the single dimension associated with a coordinate."""
    coord_dims = cube.coord_dims(coord_name)

    if len(coord_dims) != 1:
        raise ValueError(f"Expected {coord_name} to be a one-dimensional coordinate.")

    return coord_dims[0]
