#!/usr/bin/env python3

"""Tests for convection diagnostics."""

import iris

import CSET.operators.convection as convection


def test_cape_ratio():
    """Compare with precalculated ratio."""
    precalculated = iris.load_cube("tests/test_data/ECFlagB.nc")
    precalculated_2 = iris.load_cube("tests/test_data/ECFlagB_2.nc")
    SBCAPE = iris.load_cube("tests/test_data/SBCAPE.nc")
    MUCAPE = iris.load_cube("tests/test_data/MUCAPE.nc")
    MUCIN = iris.load_cube("tests/test_data/MUCIN.nc")
    assert (
        convection.cape_ratio(SBCAPE, MUCAPE, MUCIN).data.all()
        == precalculated.data.all()
    )
    assert (
        convection.cape_ratio(SBCAPE, MUCAPE, MUCIN, MUCIN_thresh=-1.5).data.all()
        == precalculated_2.data.all()
    )
