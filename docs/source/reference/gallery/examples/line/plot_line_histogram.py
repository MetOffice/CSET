"""
Histogram plot
==============

Generate histogram of region-averaged field.

.. admonition:: References

   General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``generic_surface_histogram_series.yaml``

   The following CSET operators are used:

   * :py:mod:`CSET.operators.read.read_cubes`
   * :py:mod:`CSET.operators.plot.plot_histogram_series`.

Using *cset bake* on the command line
-------------------------------------

* Access recipe file using ``cset cookbook``.
* Set required recipe inputs on command line.

Example to generate histogram plot of ``temperature_at_screen_level`` for any number of input models::

    cset cookbook generic_surface_histogram_series.yaml
    cset -v bake -i "/path/to/input/data1" "..." "/path/to/input/dataN" \\
                 -o "./output_path" \\
                 -r generic_surface_histogram_series.yaml \\
                 --VARNAME="temperature_at_screen_level" \\
                 --MODEL_NAME="['my_model_label1', '...', 'my_model_labelN']" \\
                 --SEQUENCE="realization" \\
                 --SUBAREA_TYPE='None' --SUBAREA_EXTENT='None' --SUBAREA_NAME=''

Configuring the *cset_workflow*
-------------------------------

* Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
* Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
* Set required configuration options on ``Diagnostics / Surface (2D) fields`` panel.
* Set ``HISTOGRAM_SURFACE_FIELD_SEQUENCE=False`` to generate one histogram for all times.
* Set ``HISTOGRAM_SURFACE_FIELD_SEQUENCE=True`` to generate a separate histogram for each output time.
::

    HISTOGRAM_SURFACE_FIELD = True
    HISTOGRAM_SURFACE_FIELD_SEQUENCE = False
    SURFACE_FIELDS = ["temperature_at_screen_level", ...]


Example python code
-------------------
"""

from CSET import sample_data_path
from CSET.operators import plot, read

# Set paths to input data
filename1 = sample_data_path("air_temperature_1.nc")
filename2 = sample_data_path("air_temperature_2.nc")

# Read selected variable(s) of interest for 2 models
cubes = read.read_cubes(
    [filename1, filename2],
    ["temperature_at_screen_level"],
    model_names=["model_fcst_1", "model_fcst_2"],
)

# Plot domain histogram using plot_histogram_series
plot.plot_histogram_series(cubes, sequence_coordinate="realization")
