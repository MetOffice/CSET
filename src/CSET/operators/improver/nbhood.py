# (C) Crown Copyright, Met Office. All rights reserved.
#
# This file is part of 'IMPROVER' and is released under the BSD 3-Clause license.
# See LICENSE in the root of the repository for full licensing details.
"""Module containing plugin base class."""

# This code is borrowed from https://github.com/metoppv/improver/ with some modifications.

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, Optional, Tuple, Union

import numpy as np
from iris.cube import Cube, CubeList
from numpy import ndarray
from scipy.ndimage.filters import correlate


def pad_boxsum(
    data: ndarray, boxsize: Union[int, Tuple[int, int]], **pad_options: Any
) -> ndarray:
    """Pad an array to shape suitable for `boxsum`.

    Note that padding is not symmetric: there is an extra row/column at
    the top/left (as required for calculating the boxsum).

    Args:
        data:
            The input data array.
        boxsize:
            The size of the neighbourhood.
        pad_options:
            Additional keyword arguments passed to `numpy.pad` function.

    Returns
    -------
        Array padded to shape suitable for `boxsum`.
    """
    boxsize = np.atleast_1d(boxsize)
    ih, jh = boxsize[0] // 2, boxsize[-1] // 2
    padding = [(0, 0)] * (data.ndim - 2) + [(ih + 1, ih), (jh + 1, jh)]
    padded = np.pad(data, padding, **pad_options)
    return padded


def boxsum(
    data: ndarray,
    boxsize: Union[int, Tuple[int, int]],
    cumsum: bool = True,
    **pad_options: Any,
) -> ndarray:
    """Fast vectorised approach to calculating neighbourhood totals.

    This function makes use of the summed-area table method. An input
    array is accumulated top to bottom and left to right. This accumulated
    array can then be used to efficiently calculate the total within a
    neighbourhood about any point. An example input data array::

        | 1 | 1 | 1 | 1 | 1 |
        | 1 | 1 | 1 | 1 | 1 |
        | 1 | 1 | 1 | 1 | 1 |
        | 1 | 1 | 1 | 1 | 1 |

    is accumulated to become::

        | 1 | 2  | 3  | 4  | 5  |
        | 2 | 4  | 6  | 8  | 10 |
        | 3 | 6  | 9  | 12 | 15 |
        | 4 | 8  | 12 | 16 | 20 |
        | 5 | 10 | 15 | 20 | 25 |

    If we wish to calculate the total in a 3x3 neighbourhood about
    some point (*) of our array we use the following points::

        | 1 (C) | 2  | 3     | 4 (D)  | 5  |
        | 2     | 4  | 6     | 8      | 10 |
        | 3     | 6  | 9 (*) | 12     | 15 |
        | 4 (A) | 8  | 12    | 16 (B) | 20 |
        | 5     | 10 | 15    | 20     | 25 |

    And the calculation is::

        Neighbourhood sum = C - A - D + B
        = 1 - 4 - 4 + 16
        = 9

    This is the value we would expect for a 3x3 neighbourhood
    in an array filled with ones.

    Args:
        data:
            The input data array.
        boxsize:
            The size of the neighbourhood. Must be an odd number.
        cumsum:
            If False, assume the input data is already cumulative. If True
            (default), calculate cumsum along the last two dimensions of
            the input array.
        pad_options:
            Additional keyword arguments passed to `numpy.pad` function.
            If given, the returned result will have the same shape as the input
            array.

    Returns
    -------
        Array containing the calculated neighbourhood total.

    Raises
    ------
        ValueError: If `boxsize` has non-integer type.
        ValueError: If any member of `boxsize` is not an odd number.
    """
    boxsize = np.atleast_1d(boxsize)
    if not issubclass(boxsize.dtype.type, np.integer):
        raise ValueError("The size of the neighbourhood must be of an integer type.")
    if not np.all(boxsize % 2):
        raise ValueError("The size of the neighbourhood must be an odd number.")
    if pad_options:
        data = pad_boxsum(data, boxsize, **pad_options)
    if cumsum:
        data = data.cumsum(-2).cumsum(-1)
    i, j = boxsize[0], boxsize[-1]
    m, n = data.shape[-2] - i, data.shape[-1] - j
    result = (
        data[..., i : i + m, j : j + n]
        - data[..., :m, j : j + n]
        + data[..., :m, :n]
        - data[..., i : i + m, :n]
    )
    return result


class BasePlugin(ABC):
    """An abstract class for IMPROVER plugins.
    Subclasses must be callable. We preserve the process
    method by redirecting to __call__.
    """

    def __call__(self, *args, **kwargs) -> Any:
        """Makes subclasses callable to use process
        Args:
            *args:
                Positional arguments.
            **kwargs:
                Keyword arguments.

        Returns
        -------
            Output of self.process()
        """
        return self.process(*args, **kwargs)

    @abstractmethod
    def process(self, *args, **kwargs) -> Any:
        """Abstract class for rest to implement."""
        pass


class PostProcessingPlugin(BasePlugin):
    """An abstract class for IMPROVER post-processing plugins.
    Makes generalised changes to metadata relating to post-processing.
    """

    def __call__(self, *args, **kwargs) -> Any:
        """Makes subclasses callable to use process
        Args:
            *args:
                Positional arguments.
            **kwargs:
                Keyword arguments.

        Returns
        -------
            Output of self.process() with updated title attribute
        """
        result = super().__call__(*args, **kwargs)
        if isinstance(result, Cube):
            self.post_processed_title(result)
        elif isinstance(result, Iterable) and not isinstance(result, str):
            for item in result:
                if isinstance(item, Cube):
                    self.post_processed_title(item)
        return result

    @staticmethod
    def post_processed_title(cube):
        """Updates title attribute on output cube to include
        "Post-Processed".

        """
        MANDATORY_ATTRIBUTE_DEFAULTS = {
            "title": "unknown",
            "source": "IMPROVER",
            "institution": "unknown",
        }

        default_title = MANDATORY_ATTRIBUTE_DEFAULTS["title"]
        if (
            "title" in cube.attributes.keys()
            and cube.attributes["title"] != default_title
            and "Post-Processed" not in cube.attributes["title"]
        ):
            title = cube.attributes["title"]
            cube.attributes["title"] = f"Post-Processed {title}"


def circular_kernel(ranges: int, weighted_mode: bool) -> ndarray:
    """
    Method to create a circular kernel.

    Args:
        ranges:
            Number of grid cells in the x and y direction used to create
            the kernel.
        weighted_mode:
            If True, use a circle for neighbourhood kernel with
            weighting decreasing with radius.
            If False, use a circle with constant weighting.

    Returns
    -------
        Array containing the circular smoothing kernel.
        This will have the same number of dimensions as fullranges.
    """
    # The range is square

    area = ranges * ranges
    # Define the size of the kernel based on the number of grid cells
    # contained within the desired radius.
    kernel = np.ones((int(1 + ranges * 2), (int(1 + ranges * 2))))
    # Create an open multi-dimensional meshgrid.
    open_grid = np.array(
        np.ogrid[[slice(-x, x + 1) for x in (ranges, ranges)]], dtype=object
    )
    if weighted_mode:
        # Create a kernel, such that the central grid point has the
        # highest weighting, with the weighting decreasing with distance
        # away from the central grid point.
        open_grid_summed_squared = np.sum(open_grid**2.0).astype(float)
        kernel[:] = (area - open_grid_summed_squared) / area
        mask = kernel < 0.0
    else:
        mask = np.reshape(np.sum(open_grid**2) > area, np.shape(kernel))
    kernel[mask] = 0.0
    return kernel


class NeighbourhoodProcessing(PostProcessingPlugin):
    """Class for applying neighbourhood processing to produce a smoothed field
    within the chosen neighbourhood.
    """

    def __init__(
        self,
        neighbourhood_method: str,
        radii: float,
        weighted_mode: bool = False,
        sum_only: bool = False,
        re_mask: bool = True,
    ) -> None:
        """
        Initialise class.

        Args:
            neighbourhood_method:
                Name of the neighbourhood method to use. Options: 'circular',
                'square'.
            radii:
                The radii in grid points of the neighbourhood to apply.
                Rounded up to convert into integer number of grid
                points east and north, based on the characteristic spacing
                at the zero indices of the cube projection-x and y coords.
            weighted_mode:
                If True, use a circle for neighbourhood kernel with
                weighting decreasing with radius.
                If False, use a circle with constant weighting.
            sum_only:
                If true, return neighbourhood sum instead of mean.
            re_mask:
                If re_mask is True, the original un-neighbourhood processed
                mask is applied to mask out the neighbourhood processed cube.
                If re_mask is False, the original un-neighbourhood processed
                mask is not applied. Therefore, the neighbourhood processing
                may result in values being present in areas that were
                originally masked.

        Raises
        ------
            ValueError: If the neighbourhood_method is not either
                        "square" or "circular".
            ValueError: If the weighted_mode is used with a
                        neighbourhood_method that is not "circular".
        """
        self.radius = float(radii)

        if neighbourhood_method in ["square", "circular"]:
            self.neighbourhood_method = neighbourhood_method
        else:
            msg = "{} is not a valid neighbourhood_method.".format(neighbourhood_method)
            raise ValueError(msg)
        if weighted_mode and neighbourhood_method != "circular":
            msg = (
                "weighted_mode can only be used if neighbourhood_method is circular."
                f" weighted_mode provided: {weighted_mode}, "
                f"neighbourhood_method provided: {neighbourhood_method}."
            )
            raise ValueError(msg)
        self.weighted_mode = weighted_mode
        self.sum_only = sum_only
        self.re_mask = re_mask

    def _calculate_neighbourhood(
        self, data: ndarray, mask: ndarray = None
    ) -> Union[ndarray, np.ma.MaskedArray]:
        """
        Apply neighbourhood processing.

        Ensures that masked data does not
        contribute to the neighbourhood result. Masked data is either data that
        is masked in the input data array or that corresponds to zeros in the
        input mask.

        Args:
            data:
                Input data array.
            mask:
                Mask of valid input data elements.

        Returns
        -------
            Array containing the smoothed field after the
            neighbourhood method has been applied.
        """
        if not self.sum_only:
            min_val = np.nanmin(data)
            max_val = np.nanmax(data)

        # Data mask to be eventually used for re-masking.
        # (This is OK even if mask is None, it gives a scalar False mask then.)
        # Invalid data where the mask provided == 0.
        data_mask = mask == 0
        if isinstance(data, np.ma.MaskedArray):
            # Include data mask if masked array.
            data_mask = data_mask | data.mask
            data = data.data

        # Define working type and output type.
        if issubclass(data.dtype.type, np.complexfloating):
            loc_data_dtype = np.complex128
            out_data_dtype = np.complex64
        else:
            # Use 64-bit types for enough precision in accumulations.
            loc_data_dtype = np.float64
            out_data_dtype = np.float32
        data = np.array(data, dtype=loc_data_dtype)

        # Replace invalid elements with zeros so they don't count towards
        # neighbourhood sum
        if self.neighbourhood_method == "circular":
            mask_type = np.float32
        else:
            mask_type = np.int64
        valid_data_mask = np.ones(data.shape, dtype=mask_type)
        valid_data_mask[data_mask] = 0
        data[data_mask] = 0

        if self.sum_only:
            max_extreme_data = None
        else:
            area_sum = self._do_nbhood_sum(valid_data_mask)
            max_extreme_data = area_sum.astype(loc_data_dtype)
        # Where data are all ones in nbhood, result will be same as area_sum
        data = self._do_nbhood_sum(data, max_extreme=max_extreme_data)

        if not self.sum_only:
            with np.errstate(divide="ignore", invalid="ignore"):
                # Calculate neighbourhood mean.
                data = data / area_sum
            # For points where all data in the neighbourhood is masked,
            # set result to nan
            data[area_sum == 0] = np.nan
            data = data.clip(min_val, max_val)

        if self.re_mask:
            data = np.ma.masked_array(data, data_mask, copy=False)

        return data.astype(out_data_dtype)

    def _do_nbhood_sum(
        self, data: np.ndarray, max_extreme: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """Calculate the sum-in-area from an array.

        As this can be expensive, the method first checks for the extreme cases where the data are:
        All zeros (result will be all zeros too)
        All ones (result will be max_extreme, if supplied)
        Contains outer rows / columns that are completely zero or completely one, these
        rows and columns are trimmed before calculating the area sum and their contents
        will be as for the appropriate all case above.

        Args:
            data:
                Input data array where any masking has already been replaced with zeroes.
            max_extreme:
                Used as the result for any large areas of data that are all ones, allowing an
                optimisation to be used. If not supplied, the optimisation will only be used for
                large areas of zeroes, where a return of zero can be safely predicted.

        Returns
        -------
            Array containing the sum of data within the usable neighbourhood of each point.
        """
        # Determine the smallest box containing all non-zero or all non-one values with a
        # neighbourhood-sized buffer and quit if there are none.
        data_shape = data.shape
        ystart = xstart = 0
        ystop, xstop = data.shape
        size = data.size
        extreme = 0
        fill_value = 0
        half_nb_size = self.nb_size // 2
        # For the two extreme values, 0 and 1, find the size and position of the smallest array
        # that includes all other values with a buffer of the neighbourhood radius.
        # The smallest box from either extreme will be passed to the neighbourhood method.
        for _extreme, _fill_value in {0: 0, 1: max_extreme}.items():
            if _fill_value is None or issubclass(data.dtype.type, np.complexfloating):
                # We can't take this shortcut if we don't have either a default value/array,
                # or the data values are complex, as comparisons with non-complex values are
                # tricky.
                continue
            nonextreme_indices = np.argwhere(data != _extreme)
            if nonextreme_indices.size == 0:
                # No non-extreme values, so result will be _fill_value if set
                _ystart = _ystop = _xstart = _xstop = 0
            else:
                (_ystart, _xstart), (_ystop, _xstop) = (
                    nonextreme_indices.min(0),
                    nonextreme_indices.max(0) + 1,
                )
                _ystart = max(0, _ystart - half_nb_size)
                _ystop = min(data_shape[0], _ystop + half_nb_size)
                _xstart = max(0, _xstart - half_nb_size)
                _xstop = min(data_shape[1], _xstop + half_nb_size)
            _size = (_ystop - _ystart) * (_xstop - _xstart)
            if _size < size:
                size, extreme, fill_value, ystart, ystop, xstart, xstop = (
                    _size,
                    _extreme,
                    _fill_value,
                    _ystart,
                    _ystop,
                    _xstart,
                    _xstop,
                )
        if size != data.size:
            # If our chosen extreme allows us to process a subset of data, define the default array
            # of neighbourhood sums that we know we will get for regions of extreme data values.
            if isinstance(fill_value, np.ndarray):
                untrimmed = fill_value.astype(data.dtype)
            else:
                untrimmed = np.full(data_shape, fill_value, dtype=data.dtype)
        if size:
            # The subset of data is non-zero in size, so calculate the neighbourhood sums in the
            # subset.
            data = data[ystart:ystop, xstart:xstop]

            # Calculate neighbourhood totals for input data.
            if self.neighbourhood_method == "square":
                data = boxsum(
                    data, self.nb_size, mode="constant", constant_values=extreme
                )
            elif self.neighbourhood_method == "circular":
                data = correlate(data, self.kernel, mode="nearest")
        else:
            data = untrimmed

        # Expand data to the full size again
        if data.shape != data_shape:
            untrimmed[ystart:ystop, xstart:xstop] = data
            data = untrimmed
        return data

    def process(self, cube: Cube, mask_cube: Optional[Cube] = None) -> Cube:
        """
        Call the methods required to apply a neighbourhood processing to a cube.

        Applies neighbourhood processing to each 2D x-y-slice of the input cube.

        If the input cube is masked the neighbourhood sum is calculated from
        the total of the unmasked data in the neighbourhood around each grid
        point. The neighbourhood mean is then calculated by dividing the
        neighbourhood sum at each grid point by the total number of valid grid
        points that contributed to that sum. If a mask_cube is provided then
        this is used to mask each x-y-slice prior to the neighbourhood sum
        or mean being calculated.


        Args:
            cube:
                Cube containing the array to which the neighbourhood processing
                will be applied. Usually thresholded data.
            mask_cube:
                Cube containing the array to be used as a mask. Zero values in
                this array are taken as points to be masked.

        Returns
        -------
            Cube containing the smoothed field after the
            neighbourhood method has been applied.
        """
        if np.isnan(cube.data).any():
            raise ValueError("Error: NaN detected in input cube data")

        # check_if_grid_is_equal_area(cube)

        # If the data is masked, the mask will be processed as well as the
        # original_data * mask array.
        # check_radius_against_distance(cube, self.radius)

        # grid_cells = distance_to_number_of_grid_cells(cube, self.radius)
        grid_cells = int(self.radius)

        if self.neighbourhood_method == "circular":
            self.kernel = circular_kernel(grid_cells, self.weighted_mode)
            self.nb_size = max(self.kernel.shape)
        else:
            self.nb_size = grid_cells

        try:
            mask_cube_data = mask_cube.data
        except AttributeError:
            mask_cube_data = None

        result_slices = CubeList()
        for cube_slice in cube.slices([cube.coord(axis="y"), cube.coord(axis="x")]):
            cube_slice.data = self._calculate_neighbourhood(
                cube_slice.data, mask_cube_data
            )
            result_slices.append(cube_slice)
        neighbourhood_averaged_cube = result_slices.merge_cube()

        return neighbourhood_averaged_cube
