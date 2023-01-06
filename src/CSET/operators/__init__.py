"""
This subpackage contains all of CSET's operators.
"""
from CSET.operators import read, write, filters, generate_constraints

import iris

# Stop iris giving a warning whenever it loads something.
iris.FUTURE.datum_support = True
