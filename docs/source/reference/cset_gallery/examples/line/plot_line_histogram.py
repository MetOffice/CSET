"""
Histogram plot
==============

Generate histogram of region-averaged field.

Line are generated using either CSET operators :py:mod:`CSET.operators.plot.plot_histogram_series`.

General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``generic_surface_histogram_series.yaml``


A) Using *cset bake* on the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Access recipe file using ``cset cookbook``.
- Set required recipe inputs on command-line (or as environment variables for greater flexibility).
- Use ``SEQUENCE="realization"`` to generate one histogram for all times.
- Use ``SEQUENCE="time"`` for a histogram at each output time.
- Example to generate full domain histogram of ``VARNAME`` for all output times:

.. code-block::

    cset cookbook generic_surface_histogram_series
    cset bake -i "input_data_path" ["input_data_path2" "input_data_path3" "..."] -o "my_output_path"
              -r generic_surface_histogram_series.yaml
              --VARNAME="temperature_at_screen_level"
              --MODEL_NAME="my_model_label" "my_model_label2" "my_model_label3" "..."
              --SEQUENCE="realization"
              --SUBAREA_TYPE='None' --SUBAREA_EXTENT='None' --SUBAREA_NAME='None'
              [-s STYLE_FILE] [--plot-resolution PLOT_RESOLUTION] [--skip-write]



B) Configuring the *cset_workflow*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
- Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
- Set required configuration options on ``Diagnostics / Surface (2D) fields`` panel.
- Set ``HISTOGRAM_SURFACE_FIELD_SEQUENCE=False`` to generate one histogram for all times.
- Set ``HISTOGRAM_SURFACE_FIELD_SEQUENCE=True`` for a histogram at each output time.

::

    SURFACE_FIELDS = ['temperature_at_screen_level', <other_variable_of_interest>, ...]
    HISTOGRAM_SURFACE_FIELD = True
    HISTOGRAM_SURFACE_FIELD_SEQUENCE = False



C) Example python code
^^^^^^^^^^^^^^^^^^^^^^
"""

import CSET.operators.plot as cset_plot
import CSET.operators.read as cset_read

# Set path to input data
file_paths = "../../../../../../tests/test_data/air_temperature_global.nc"

# Read selected variable(s) of interest
cubes = cset_read.read_cubes(file_paths, ["temperature_at_screen_level"])

# Plot domain histogram
cset_plot.plot_histogram_series(cubes, sequence_coordinate="realization")
