import multiprocessing as mp
import os
from functools import partial
from typing import List, Union

import cartopy.crs as ccrs
import iris
import iris.coords as icoords
import iris.cube
import numpy as np
import numpy.ma as ma
from improver.nbhood.nbhood import NeighbourhoodProcessing
from iris import coord_systems
from scipy import ndimage, signal

# from .neighbourhooding import SquareNeighbourhood

"""A module containing the dFSS diagnostic
"""


def _get_neighbourhood_data(
    cube: iris.cube.Cube,
    max_or_mean: str,
    neighbourhood_length: int,
):

    if type(neighbourhood_length) is not int:
        raise TypeError(
            "neighbourhood_length expected to be an int, got {}".format(
                type(neighbourhood_length).__name__
            )
        )

    if max_or_mean not in ["mean", "max"]:
        raise ValueError(
            "Key word for neighbourhood processing should be 'max' or 'mean'"
        )

    kernel = np.ones((neighbourhood_length, neighbourhood_length))

    if max_or_mean == "mean":
        neighbourhood_data = (
            signal.convolve2d(cube.data, kernel, boundary="wrap", mode="same")
            / kernel.sum()
        )
    elif max_or_mean == "max":
        neighbourhood_data = ndimage.maximum_filter(
            cube.data, footprint=kernel, mode="wrap"
        )

        neighbourhood_data = ndimage.uniform_filter(
            neighbourhood_data.data, size=neighbourhood_length, mode="constant"
        )

    return neighbourhood_data


def neighbourhood(
    cube: iris.cube.Cube, neighbourhood_length: int, max_or_mean: str = "mean"
) -> iris.cube.Cube:

    cube_list = iris.cube.CubeList()
    if cube.coord("realization") and cube.coord("realization").points.size > 1:
        for cb in cube.slices_over("realization"):
            neighbourhood_data = _get_neighbourhood_data(
                cb, max_or_mean, neighbourhood_length
            )
            cb_new = cb.copy(data=neighbourhood_data)
            cube_list.append(cb_new)

        cube_list.append(cube_list.merge_cube())
    else:
        neighbourhood_data = _get_neighbourhood_data(
            cube, max_or_mean, neighbourhood_length
        )
        return cube.copy(data=neighbourhood_data)

    return cube_list.merge_cube()


def init_worker():
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    os.environ["OPENBLAS_NUM_THREADS"] = "1"


def dfss_on_slice(
    slice,
    neighbourhood_lengths,
    centile_or_threshold,
    centile,
    threshold,
    max_or_mean="mean",
):
    time_point = slice.coord("time")
    dfss_cube, dfss_stdev_cube = _calc_dfss(
        slice,
        neighbourhood_lengths,
        time_point,
        centile_or_threshold,
        centile,
        threshold,
    )

    return dfss_cube, dfss_stdev_cube


def _parallel_calculate_dfss(
    cube_xy: iris.cube.Cube,
    neighbourhood_lengths: List[int],
    centile_or_threshold: str = "centile",
    centile: Union[float, int] = None,
    threshold: Union[float, int] = None,
):

    time_slices = list(cube_xy.slices_over("time"))

    with mp.Pool(initializer=init_worker) as pool:
        worker = partial(
            dfss_on_slice,
            neighbourhood_lengths=neighbourhood_lengths,
            centile_or_threshold=centile_or_threshold,
            centile=centile,
            threshold=threshold,
            max_or_mean="mean",
        )
        dfss_cubes, dfss_stdev_cubes = zip(*pool.imap(worker, time_slices))

    cube_list_dfss = iris.cube.CubeList(dfss_cubes)
    cube_list_dfss_stdev = iris.cube.CubeList(dfss_stdev_cubes)

    forecast_period = cube_xy.coord("forecast_period")
    merged_cube_dfss = cube_list_dfss.merge_cube()

    merged_cube_dfss_stdev = cube_list_dfss_stdev.merge_cube()

    merged_cube_dfss.add_aux_coord(forecast_period, data_dims=(0))
    merged_cube_dfss_stdev.add_aux_coord(forecast_period, data_dims=(0))

    out_cube_list = iris.cube.CubeList()

    out_cube_list.append(merged_cube_dfss)
    out_cube_list.append(merged_cube_dfss_stdev)

    return out_cube_list


def _serial_calculate_dfss(
    cube_xy: iris.cube.Cube,
    neighbourhood_lengths: List[int],
    centile_or_threshold: str = "centile",
    centile: Union[float, int] = None,
    threshold: Union[float, int] = None,
):

    cube_list_dfss = iris.cube.CubeList()
    cube_list_dfss_stdev = iris.cube.CubeList()

    for time_slice in cube_xy.slices_over("time"):
        time_point = time_slice.coord("time")
        print("time_point = " + str(time_point.points))
        dfss_cube, dfss_stdev_cube = _calc_dfss(
            time_slice,
            neighbourhood_lengths,
            time_point,
            centile_or_threshold,
            centile,
            threshold,
        )  #
        cube_list_dfss.append(dfss_cube)
        cube_list_dfss_stdev.append(dfss_stdev_cube)

    forecast_period = cube_xy.coord("forecast_period")

    merged_cube_dfss = cube_list_dfss.merge_cube()
    merged_cube_dfss_stdev = cube_list_dfss_stdev.merge_cube()

    merged_cube_dfss.add_aux_coord(forecast_period, data_dims=(0))
    merged_cube_dfss_stdev.add_aux_coord(forecast_period, data_dims=(0))

    out_cube_list = iris.cube.CubeList()

    out_cube_list.append(merged_cube_dfss)
    out_cube_list.append(merged_cube_dfss_stdev)

    return out_cube_list


def calculate_dfss(
    cube_xy: iris.cube.Cube,
    neighbourhood_lengths: List[int],
    centile_or_threshold: str = "centile",
    centile: Union[float, int] = None,
    threshold: Union[float, int] = None,
    run_parallel: bool = True,
):

    if run_parallel:
        out_cube_list = _parallel_calculate_dfss(
            cube_xy, neighbourhood_lengths, centile_or_threshold, centile, threshold
        )
    else:
        out_cube_list = _serial_calculate_dfss(
            cube_xy, neighbourhood_lengths, centile_or_threshold, centile, threshold
        )
    return out_cube_list


def _calc_dfss(
    cube_xy: iris.cube.Cube,
    neighbourhood_lengths: Union[List[int]],
    time_point,
    centile_or_threshold: str = "centile",
    centile: Union[float, int] = None,
    threshold: Union[float, int] = None,
):
    cube_xy.data  # NOTE: without realising the data, dask is very slow to run this code
    ens_members = cube_xy.coord("realization").points
    number_of_members = len(ens_members)
    dfss = np.zeros(len(neighbourhood_lengths))
    dfss_stdev = np.zeros_like(dfss)

    for i, neighbourhood_length in enumerate(neighbourhood_lengths):
        fss_array = np.full((number_of_members, number_of_members), np.nan)
        iu1 = np.triu_indices(number_of_members, 1)

        fss_array[iu1] = 0.0
        for i_a, memb_a in enumerate(ens_members):
            ens_member_a = cube_xy.extract(iris.Constraint(realization=memb_a))
            for i_b, memb_b in enumerate(ens_members):
                if not np.isnan(fss_array[i_a, i_b]):
                    ens_member_b = cube_xy.extract(iris.Constraint(realization=memb_b))

                    fss_array[i_a, i_b] = _calc_fss(
                        ens_member_a,
                        ens_member_b,
                        neighbourhood_length,
                        centile_or_threshold=centile_or_threshold,
                        centile=centile,
                        threshold=threshold,
                    )

                    if fss_array[i_a, i_b] == np.nan:
                        dfss[:] = np.nan
                        dfss_stdev[:] = np.nan
                        return dfss, dfss_stdev

        dfss[i] = (ma.masked_invalid(fss_array)).mean()
        dfss_stdev[i] = (ma.masked_invalid(fss_array)).std()

    neighbourhood_coord = icoords.DimCoord(
        neighbourhood_lengths, var_name="neighbourhoods"
    )

    dfss_cube = iris.cube.Cube(
        dfss, long_name="dfss", dim_coords_and_dims=[(neighbourhood_coord, 0)]
    )
    dfss_cube.add_aux_coord(time_point)
    dfss_stdev_cube = iris.cube.Cube(
        dfss_stdev,
        long_name="dfss_stdev",
        dim_coords_and_dims=[(neighbourhood_coord, 0)],
    )
    dfss_stdev_cube.add_aux_coord(time_point)
    return dfss_cube, dfss_stdev_cube


def _calc_fss(
    cube_a_in: iris.cube.Cube,
    cube_b_in: iris.cube.Cube,
    neighbourhood_length: int,
    centile_or_threshold: str = "centile",
    centile: float = None,
    threshold: float = None,
):
    # Set the threshold of interest

    cube_a = cube_a_in.copy()
    cube_b = cube_b_in.copy()

    if centile_or_threshold == "centile":
        cube_a_has_mask = isinstance(cube_a.data, np.ma.MaskedArray)
        cube_b_has_mask = isinstance(cube_b.data, np.ma.MaskedArray)
        if cube_a_has_mask and cube_b_has_mask:
            threshold_a = np.nanpercentile(cube_a.data.filled(np.nan), centile)
            threshold_b = np.nanpercentile(cube_b.data.filled(np.nan), centile)
        elif not cube_a_has_mask and not cube_b_has_mask:
            threshold_a = np.percentile(cube_a.data, centile)
            threshold_b = np.percentile(cube_b.data, centile)
        else:
            msg = "Mask status must be the same for both cubes"
            raise UserWarning(msg)
    elif centile_or_threshold == "threshold":
        threshold_a = threshold_b = threshold
    else:
        msg = (
            "Function argument centile_or_threshold must equal one "
            "of [centile, threshold]"
        )
        raise UserWarning(msg)

    cube_a.data = np.ma.where(cube_a.data > threshold_a, 1, 0)
    cube_b.data = np.ma.where(cube_b.data > threshold_b, 1, 0)

    n_a = np.count_nonzero(cube_a.data)
    n_b = np.count_nonzero(cube_b.data)

    n_tot = np.size(cube_a.data)
    frac_cov_a = n_a / n_tot
    frac_cov_b = n_b / n_tot

    if np.maximum(frac_cov_a, frac_cov_b) <= 0.002:
        fss = np.nan
        return fss

    nbhooder = NeighbourhoodProcessing(
        neighbourhood_method="square", radii=neighbourhood_length
    )

    cube_a = regrid_lat_lon_cube_to_xy_cube(cube_a)
    cube_b = regrid_lat_lon_cube_to_xy_cube(cube_b)

    fraction_fields_a = nbhooder.process(cube_a)
    fraction_fields_b = nbhooder.process(cube_b)
    field_a = neighbourhood(cube_a, neighbourhood_length)
    field_b = neighbourhood(cube_b, neighbourhood_length)

    field_a = fraction_fields_a.data
    field_b = fraction_fields_b.data

    fss = _calc_fss_two_fields(field_a.data, field_b.data)

    # nbhooder = SquareNeighbourhood(sum_or_fraction="fraction")
    # radius_grid_point = int((neighbourhood_length - 1) / 2)
    # fraction_fields_a = nbhooder.run(cube_a, radius_grid_point, radius_grid_point)
    # fraction_fields_b = nbhooder.run(cube_b, radius_grid_point, radius_grid_point)

    # Calculate the FSS between the two fields
    # field_a = fraction_fields_a.data
    # field_b = fraction_fields_b.data

    # fss = _calc_fss_two_fields(field_a, field_b)

    return fss


def _calc_fss_two_fields(field_a, field_b):
    field_diff = field_a - field_b
    mse = np.sum(np.sum(field_diff**2))
    abs_val = field_a**2 + field_b**2
    mse_ref = np.sum(np.sum(abs_val))
    if mse_ref > 0:
        fss = 1 - (mse / mse_ref)
    else:
        fss = np.nan

    return fss


def get_spatial_coords(cube):
    """Returns the x, y coordinates of an input :class:`iris.cube.Cube`."""
    x_coord = cube.coord(axis="x")
    y_coord = cube.coord(axis="y")
    return [x_coord, y_coord]


def regrid_lat_lon_cube_to_xy_cube(cube_latlon):
    """
    Takes a cube specified on a lat-lon grid and re-grids
    it to an x-y grid

    Args:
        cube_latlon:
            Original cube on a lat-lon grid

    Returns
    -------
        cube_xy:
            Original cube regridded onto an x-y grid

    """
    x_coord, y_coord = get_spatial_coords(cube_latlon)

    # Transform max and min lon and lat points to set new x,y array on
    # new coordinate system
    src_crs = y_coord.coord_system.as_cartopy_crs()
    trg_crs = ccrs.TransverseMercator(central_latitude=0, central_longitude=0)
    trg_crs_iris = coord_systems.TransverseMercator(0, 0, 0, 0, 1.0)

    lons = [np.min(x_coord.points), np.max(x_coord.points)]
    lats = [np.min(y_coord.points), np.max(y_coord.points)]

    x, y = [], []
    for lon, lat in zip(lons, lats):
        x_trg, y_trg = trg_crs.transform_point(lon, lat, src_crs)
        x.append(x_trg)
        y.append(y_trg)

    numb_x_points = np.size(x_coord.points)
    numb_y_points = np.size(y_coord.points)
    total_numb_points = numb_x_points * numb_y_points

    new_x = icoords.DimCoord(
        np.linspace(x[0], x[1], numb_x_points),
        standard_name="projection_x_coordinate",
        units="m",
        coord_system=trg_crs_iris,
    )

    new_y = icoords.DimCoord(
        np.linspace(y[0], y[1], numb_y_points),
        standard_name="projection_y_coordinate",
        units="m",
        coord_system=trg_crs_iris,
    )

    new_ens = icoords.DimCoord(
        cube_latlon.coord("realization").points, standard_name="realization"
    )

    number_members = len(cube_latlon.coord("realization").points)
    new_data = np.zeros(number_members * total_numb_points).reshape(
        number_members, numb_y_points, numb_x_points
    )

    # Create blank cube in new coordinate system
    new_cube = iris.cube.Cube(
        new_data,
        long_name=cube_latlon.name(),
        dim_coords_and_dims=[(new_ens, 0), (new_y, 1), (new_x, 2)],
        units=cube_latlon.units,
    )

    # Regrid original cube onto new cube
    cube_xy = cube_latlon.regrid(new_cube, iris.analysis.Nearest())

    return cube_xy
