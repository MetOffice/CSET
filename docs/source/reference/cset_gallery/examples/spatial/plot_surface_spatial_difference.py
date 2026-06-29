"""
Regional spatial plot
=====================

Generate spatial map of a 2D field difference (regional data example).

Spatial maps are generated using either CSET operators :py:mod:`CSET.operators.plot.spatial_pcolormesh_plot` or :py:mod:`CSET.operators.plot.spatial_contour_plot`.

General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``generic_surface_spatial_difference.yaml``


A) Using *cset bake* on the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Access recipe file using ``cset cookbook``.
- Set required recipe inputs on command-line (or as environment variables for greater flexibility).
- Example to generate full-domain spatial maps of ``VARNAME`` for all output times:

.. code-block::

    cset cookbook generic_surface_spatial_difference
    cset bake -i "input_data_path_1" "input_data_path_2" -o "my_output_path"
              -r generic_surface_spatial_difference
              --VARNAME="air_temperature"
              --BASE_MODEL="Model 1"
              --OTHER_MODEL="Model 2"
              --MODEL_NAME="my_model_label"
              --METHOD=""
              --SUBAREA_TYPE='None' --SUBAREA_EXTENT='None' --SUBAREA_NAME='None'
              [-s STYLE_FILE] [--plot-resolution PLOT_RESOLUTION] [--skip-write]

B) Configuring the *cset_workflow*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
- Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
- Set required configuration options on ``Diagnostics / Surface (2D) fields`` panel:

::

    SURFACE_FIELDS = ['air_temperature', <other_variable_of_interest>, ...]
    SPATIAL_DIFFERENCE_SURFACE_FIELD = True


C) Example python code
^^^^^^^^^^^^^^^^^^^^^^
"""

import CSET.operators.constraints as cset_constrain
import CSET.operators.misc as cset_misc
import CSET.operators.plot as cset_plot
import CSET.operators.read as cset_read

# Set path to input data
file_path = [
    "/home/users/mike.bush/repos/CSET/tests/test_data/air_temp.nc",
    "/home/users/mike.bush/repos/CSET//tests/test_data/air_temp_a.nc",
]

# Generating constraints that Iris can understand that can be used later in the code
constraint_nomethods = cset_constrain.generate_cell_methods_constraint([])
constraint_var = cset_constrain.generate_var_constraint("air_temperature")
both_constraints = cset_constrain.combine_constraints(
    constraint=constraint_nomethods, additional_constraint_1=constraint_var
)

# Read selected variable(s) of interest
cubes = cset_read.read_cubes(file_path, constraint=both_constraints)

#
diff = cset_misc.difference(cubes)

# Plot single example frame (final time output only, using spatial_contour_plot)
cset_plot.spatial_contour_plot(diff)
