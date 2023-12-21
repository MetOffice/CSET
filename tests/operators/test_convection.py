#!/usr/bin/env python3

"""Tests for convection diagnostics."""

import iris

import CSET.operators.convection as convection


def test_cape_ratio():
    """Compare with precalculated ratio."""
    precalculated = iris.load_cube("tests/test_data/convection/ECFlagB.nc")
    precalculated_2 = iris.load_cube("tests/test_data/convection/ECFlagB_2.nc")
    SBCAPE = iris.load_cube("tests/test_data/convection/SBCAPE.nc")
    MUCAPE = iris.load_cube("tests/test_data/convection/MUCAPE.nc")
    MUCIN = iris.load_cube("tests/test_data/convection/MUCIN.nc")
    assert (
        convection.cape_ratio(SBCAPE, MUCAPE, MUCIN).data.all()
        == precalculated.data.all()
    )
    assert (
        convection.cape_ratio(SBCAPE, MUCAPE, MUCIN, MUCIN_thresh=-1.5).data.all()
        == precalculated_2.data.all()
    )


def test_inflow_layer_properties():
    """Compare with precalculated properties."""
    precalculated = iris.load_cube("tests/test_data/convection/ECFlagD.nc")
    EIB = iris.load_cube("tests/test_data/convection/EIB.nc")
    BLheight = iris.load_cube("tests/test_data/convection/BLheight.nc")
    Orography = iris.load_cube("tests/test_data/convection/Orography.nc")
    assert (
        convection.inflow_layer_properties(EIB, BLheight, Orography).all()
        == precalculated.data.all()
    )
