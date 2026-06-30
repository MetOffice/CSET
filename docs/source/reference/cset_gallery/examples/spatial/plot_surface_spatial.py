"""
Regional spatial plot
=====================

Generate spatial map of a 2D field (regional data example).

Spatial maps are generated using either CSET operators :py:mod:`CSET.operators.plot.spatial_pcolormesh_plot` or :py:mod:`CSET.operators.plot.spatial_contour_plot`.

General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``generic_surface_spatial_plot_sequence.yaml``


A) Using *cset bake* on the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Access recipe file using ``cset cookbook``.
- Set required recipe inputs on command-line (or as environment variables for greater flexibility).
- Example to generate full-domain spatial maps of ``VARNAME`` for all output times:

.. code-block::

    cset cookbook generic_surface_spatial_plot_sequence
    cset bake -i "input_data_path" -o "my_output_path"
              -r generic_surface_spatial_plot_sequence
              --VARNAME="temperature_at_screen_level"
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

    SURFACE_FIELDS = ['temperature_at_screen_level', <other_variable_of_interest>, ...]
    SPATIAL_SURFACE_FIELD = True


C) Example python code
^^^^^^^^^^^^^^^^^^^^^^
"""

import CSET.operators.plot as cset_plot
import CSET.operators.read as cset_read

# Set path to input data
file_path = "../../../../../../tests/test_data/air_temp.nc"

# Read selected variable(s) of interest
cube = cset_read.read_cubes(file_path, ["temperature_at_screen_level"])[0]

# Plot single example frame (final time output only, using spatial_contour_plot)
cset_plot.spatial_contour_plot(cube[-1])
