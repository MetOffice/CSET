"""
Vertical profile plot
=====================

Generate vertical profile of region-averaged field.

Line are generated using either CSET operators :py:mod:`CSET.operators.plot.plot_vertical_line_series`.

General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``generic_level_domain_mean_vertical_profile_series.yaml``


A) Using *cset bake* on the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Access recipe file using ``cset cookbook``.
- Set required recipe inputs on command-line (or as environment variables for greater flexibility).
- Example to generate domain mean vertical profiles of ``VARNAME`` for all output times:

.. code-block::

    cset cookbook generic_level_domain_mean_vertical_profile_series
    cset -v bake -i "input_data_path" ["input_data_path2" "input_data_path3" "..."] -o "my_output_path"
              -r generic_level_domain_mean_vertical_profile_series
              --VARNAME="air_temperature"
              --MODEL_NAME="my_model_label" "my_model_label2" "my_model_label3" "..."
              --LEVELTYPE="pressure"
              --SUBAREA_TYPE='None' --SUBAREA_EXTENT='None' --SUBAREA_NAME='None'
              [-s STYLE_FILE] [--plot-resolution PLOT_RESOLUTION] [--skip-write]


B) Configuring the *cset_workflow*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
- Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
- Set required configuration options on ``Diagnostics / Surface (2D) fields`` panel:

::

    PRESSURE_LEVEL_FIELDS = ['air_temperature', <other_variable_of_interest>, ...]
    PRESSURE_LEVELS = ['1000','850', <other_pressure_levels>, ...]
    PROFILE_PLEVEL = True


C) Example python code
^^^^^^^^^^^^^^^^^^^^^^
"""

import CSET.operators.collapse as cset_collapse
import CSET.operators.plot as cset_plot
import CSET.operators.read as cset_read

# Set path to input data
file_paths = "../../../../../../tests/test_data/transect_out_umpl.nc"

# Read selected variable(s) of interest
cubes = cset_read.read_cubes(file_paths, ["air_temperature"])

# Collapse input data over selected dimensions
collapsed_cubes = cset_collapse.collapse(cubes, ["longitude", "time"], "MEAN")

# Plot domain mean time series
cset_plot.plot_vertical_line_series(collapsed_cubes, series_coordinate="pressure")
