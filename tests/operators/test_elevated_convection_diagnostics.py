#!/usr/bin/env python3

"""Tests for elevated convection diagnostics."""

import CSET.operators.elevated_convection_diagnostics as ecd
import iris


def test_cape_ratio():
    """Compare with precalculated ratio."""
    precalculated = iris.load_cube("tests/test_data/ECFlagB.pp")
    precalculated_2 = iris.load_cube("tests/test_data/ECFlagB_2.pp")
    SBCAPE = iris.load_cube("tests/test_data/SBCAPE.pp")
    MUCAPE = iris.load_cube("tests/test_data/MUCAPE.pp")
    MUCIN = iris.load_cube("tests/test_data/MUCIN.pp")
    assert ecd.cape_ratio(SBCAPE, MUCAPE, MUCIN).data.all() == precalculated.data.all()
    assert (
        ecd.cape_ratio(SBCAPE, MUCAPE, MUCIN, MUCIN_thresh=-1.5).data.all()
        == precalculated_2.data.all()
    )
