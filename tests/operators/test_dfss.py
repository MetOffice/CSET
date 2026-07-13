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

"""Tests for the dFSS operator."""

import iris
import iris.cube
import numpy as np
import pytest

from CSET.operators import dfss


@pytest.mark.filterwarnings("ignore: Warning")
def test_dfss_basic_functioning(dfss_ensemble_cube):
    """Test basic functionality of the main dfss function."""
    fc_time_npoints = dfss_ensemble_cube.shape[1]
    neighbourhood_lengths = [1, 2, 3]

    dfss_cube, dfss_stdev_cube = dfss.calculate_dfss(
        dfss_ensemble_cube,
        neighbourhood_lengths=neighbourhood_lengths,
        centile=95,
        run_parallel=False,
    )

    assert dfss_cube.data.shape == (fc_time_npoints, np.size(neighbourhood_lengths))
    assert dfss_stdev_cube.data.shape == (
        fc_time_npoints,
        np.size(neighbourhood_lengths),
    )


def test_dfss_one_realisation_exception(dfss_ensemble_cube):
    """Test handling of non-ensemble data."""
    one_realisation_dfss_ensemble_cube = dfss_ensemble_cube.extract(
        iris.Constraint(realization=1)
    )
    with pytest.raises(ValueError, match=r"dFSS is only valid for an ensemble"):
        dfss.calculate_dfss(
            one_realisation_dfss_ensemble_cube,
            neighbourhood_lengths=[0, 1, 2],
            centile=95,
            run_parallel=False,
        )


def test_calc_fss(dfss_ensemble_cube):
    """Test the calc_fss function."""
    cube_a_in = dfss_ensemble_cube[1, :, :, :]
    cube_b_in = dfss_ensemble_cube[2, :, :, :]
    fss = dfss._calc_fss(cube_a_in, cube_b_in, neighbourhood_length=2, centile=95)
    assert type(fss) is float
