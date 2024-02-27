#!/usr/bin/env python3

"""Tests regrid operator."""

import iris
import CSET.operators.regrid as regrid


def test_regrid_onto_xyspacing():
    """Test regrid case where x and y spacing are specified"""

    # Test 1: Rectilinear GeogCS grid case
    test_data = iris.load_cube("tests/test_data/regrid/regrid_rectilinearGeogCS.nc")
    regridded_test_data = iris.load_cube("tests/test_data/regrid/out_rectilinearGeogCS_0p5deg.nc")

    assert (
        regrid.regrid_onto_xyspacing(test_data,xpacing=0.5,yspacing=0.5,regridmethod='Linear').data.all()
        == regridded_test_data.data.all()
    )

def test_regrid_onto_cube():
    """Test regrid case where target cube to project onto is specified"""

    # Test 1: Rectilinear GeogCS grid case
    test_data = iris.load_cube("tests/test_data/regrid/regrid_rectilinearGeogCS.nc")
    regridded_test_data = iris.load_cube("tests/test_data/regrid/out_rectilinearGeogCS_0p5deg.nc")

    assert (
        regrid.regrid_onto_cube(test_data,regridded_test_data,regridmethod='Linear').data.all()
        == regridded_test_data.data.all()
    )
