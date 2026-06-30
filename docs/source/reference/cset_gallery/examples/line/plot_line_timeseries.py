"""
Time series plot
================

Generate time series of region-averaged field.

Line are generated using either CSET operators :py:mod:`CSET.operators.plot.plot_line_series`.

General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``generic_surface_domain_mean_time_series.yaml``


A) Using *cset bake* on the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Access recipe file using ``cset cookbook``.
- Set required recipe inputs on command-line (or as environment variables for greater flexibility).
- Example to generate full-domain spatial maps of ``VARNAME`` for all output times:

.. code-block::

    cset cookbook generic_surface_domain_mean_time_series
    cset -v bake -i "input_data_path" ["input_data_path2" "input_data_path3" "..."] -o "my_output_path"
              -r generic_surface_domain_mean_time_series.yaml
              --VARNAME="temperature_at_screen_level"
              --MODEL_NAME="my_model_label" "my_model_label2" "my_model_label3" "..."
              --SUBAREA_TYPE='None' --SUBAREA_EXTENT='None' --SUBAREA_NAME='None'
              [-s STYLE_FILE] [--plot-resolution PLOT_RESOLUTION] [--skip-write]


B) Configuring the *cset_workflow*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
- Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
- Set required configuration options on ``Diagnostics / Surface (2D) fields`` panel:

::

    SURFACE_FIELDS = ['temperature_at_screen_level', <other_variable_of_interest>, ...]
    TIMESERIES_SURFACE_FIELD = True


C) Example python code
^^^^^^^^^^^^^^^^^^^^^^
"""

import CSET.operators.collapse as cset_collapse
import CSET.operators.plot as cset_plot
import CSET.operators.read as cset_read

# Set path to input data
file_paths = [
    "../../../../../../tests/test_data/long_forecast_air_temp_fcst_1.nc",
    "../../../../../../tests/test_data/long_forecast_air_temp_fcst_a.nc",
]

# Read selected variable(s) of interest
cubes = cset_read.read_cubes(
    file_paths, ["temperature_at_screen_level"], model_names=["model_1", "model_a"]
)

# Collapse input data over selected dimensions
collapsed_cubes = cset_collapse.collapse(
    cubes, ["grid_latitude", "grid_longitude"], "MEAN"
)

# Plot domain mean time series
cset_plot.plot_line_series(collapsed_cubes)
