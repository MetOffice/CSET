"""
Vertical profile plot
=====================

Generate vertical profile of region-averaged field.

.. admonition:: References

   General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``generic_level_domain_mean_vertical_profile_series.yaml``

   The following CSET operators are used:

   * :py:mod:`CSET.operators.read.read_cubes`
   * :py:mod:`CSET.operators.collapse.collapse`
   * :py:mod:`CSET.operators.plot.plot_vertical_line_series`.

Using *cset bake* on the command line
-------------------------------------

* Access recipe file using ``cset cookbook``.
* Set required recipe inputs on command line.

Example to generate vertical profile plot of domain averaged ``air_temperature`` on pressure levels for any number of input models::

    cset cookbook generic_level_domain_mean_vertical_profile_series.yaml
    cset -v bake -i "/path/to/input/data1" "..." "/path/to/input/dataN" \\
                 -o "./output_path" \\
                 -r generic_level_domain_mean_vertical_profile_series.yaml \\
                 --VARNAME="air_temperature" \\
                 --MODEL_NAME="['my_model_label1' '...' 'my_model_labelN']" \\
                 --LEVELTYPE="pressure" \\
                 --METHOD="SEQ" \\
                 --SUBAREA_TYPE='None' --SUBAREA_EXTENT='None' --SUBAREA_NAME=''

Configuring the *cset_workflow*
-------------------------------

* Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
* Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
* To plot vertical profile of fields defined on pressure levels, set required configuration options on ``Diagnostics / Pressure level fields`` panel::

    PRESSURE_LEVEL_FIELDS = ["air_temperature", ...]
    PRESSURE_LEVELS = ['1000', '850', '500', ...]
    PROFILE_PLEVEL = True

* To plot vertical profile of fields defined on model levels, set required configuration options on ``Diagnostics / Model level fields`` panel::

    MODEL_LEVEL_FIELDS = ["air_temperature", ...]
    MODEL_LEVELS = [1, 2, 3, ...]
    PROFILE_MLEVEL = True


Example python code
-------------------
"""

from CSET import sample_data_path
from CSET.operators import collapse, plot, read

# Set paths to input data
filename1 = sample_data_path("profile_air_temperature_1.nc")
filename2 = sample_data_path("profile_air_temperature_2.nc")

# Read selected variable(s) of interest for 2 models
cubes = read.read_cubes(
    [filename1, filename2],
    ["air_temperature"],
    model_names=["model_fcst_1", "model_fcst_2"],
)

# Collapse input data over selected dimensions
collapsed_cubes = collapse.collapse(
    cubes, ["grid_longitude", "grid_latitude", "time"], "MEAN"
)

# Plot domain mean profile using plot_vertical_line_series
plot.plot_vertical_line_series(collapsed_cubes, series_coordinate="pressure")
