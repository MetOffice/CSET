"""
Time series plot
================

Generate time series of region-averaged field.

.. admonition:: References

   General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``generic_surface_domain_mean_time_series.yaml``

   The following CSET operators are used:

   * :py:mod:`CSET.operators.read.read_cubes`
   * :py:mod:`CSET.operators.collapse.collapse`
   * :py:mod:`CSET.operators.plot.plot_line_series`.

Using *cset bake* on the command line
-------------------------------------

* Access recipe file using ``cset cookbook``.
* Set required recipe inputs on command line.

Example to generate full-domain spatial maps of ``temperature_at_screen_level`` for all output times::

    cset cookbook generic_surface_domain_mean_time_series.yaml
    cset -v bake -i "/path/to/input/data" ["/path/to/input/data2" "..."]
                 -o "./output_path" \\
                 -r generic_surface_domain_mean_time_series.yaml \\
                 --VARNAME="temperature_at_screen_level" \\
                 --MODEL_NAME="my_model_label" ["my_model_label2" "..."] \\
                 --METHOD="SEQ" \\
                 --SUBAREA_TYPE='None' --SUBAREA_EXTENT='None' --SUBAREA_NAME='None'

Configuring the *cset_workflow*
-------------------------------

* Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
* Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
* Set required configuration options on ``Diagnostics / Surface (2D) fields`` panel::

    SURFACE_FIELDS = ["temperature_at_screen_level", ...]
    TIMESERIES_SURFACE_FIELD = True

Example python code
-------------------
"""

from CSET import sample_data_path
from CSET.operators import collapse, plot, read

# Set paths to input data
filename1 = sample_data_path("air_temperature_fcst_1.nc")
filename2 = sample_data_path("air_temperature_fcst_2.nc")

# Read selected variable(s) of interest for 2 models
cubes = read.read_cubes(
    [filename1, filename2],
    ["temperature_at_screen_level"],
    model_names=["model_fcst_1", "model_fcst_2"],
)

# Collapse input data over selected dimensions
collapsed_cubes = collapse.collapse(cubes, ["grid_latitude", "grid_longitude"], "MEAN")

# Plot domain mean time series using plot_line_series
plot.plot_line_series(collapsed_cubes)
