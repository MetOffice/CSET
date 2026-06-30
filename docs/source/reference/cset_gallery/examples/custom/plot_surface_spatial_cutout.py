"""
Trim edge gridcells
===================

Generate spatial map of a 2D field over selected sub-region of data with domain edges trimmed.

Spatial maps are generated using either CSET operators :py:mod:`CSET.operators.plot.spatial_pcolormesh_plot` or :py:mod:`CSET.operators.plot.spatial_contour_plot`.

General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``generic_surface_spatial_plot_sequence.yaml``


A) Using *cset bake* on the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- See :doc:`/reference/cset_gallery/generated/spatial/plot_surface_spatial` for general settings.
- Set ``SUBAREA_TYPE`` and ``SUBAREA_EXTENT`` to select trim widths, and use ``SUBAREA_NAME`` to control labelling.
- Example to generate spatial maps for selected sub-area of ``VARNAME`` for all output times:

.. code-block::

    cset cookbook generic_surface_spatial_plot_sequence
    cset bake -i "input_data_path" -o "my_output_path"
              -r generic_surface_spatial_plot_sequence
              --VARNAME="temperature_at_screen_level"
              --MODEL_NAME="my_model_label"
              --METHOD=""
              --SUBAREA_TYPE='gridcells' --SUBAREA_EXTENT=[3, 2, 3, 1] --SUBAREA_NAME=''
              [-s STYLE_FILE] [--plot-resolution PLOT_RESOLUTION] [--skip-write]


B) Configuring the *cset_workflow*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
- Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
- Set ``SELECT_SUBAREA`` to ``True``, set ``SUBAREA_TYPE`` to ``gridcells`` and set ``SUBAREA_EXTENT``.
- Set other required configuration options on ``Diagnostics / Surface (2D) fields`` panel.

::

    SELECT_SUBAREA = True
    SPATIAL_SURFACE_FIELD = True
    SUBAREA_TYPE = 'gridcells'
    SUBAREA_EXTENT = [3, 2, 3, 1]
    SUBAREA_NAME = ''
    SURFACE_FIELDS = ['temperature_at_screen_level', <other_variable_of_interest>, ...]


C) Example python code
^^^^^^^^^^^^^^^^^^^^^^
"""

import CSET.operators.plot as cset_plot
import CSET.operators.read as cset_read

# Set path to input data
file_path = "../../../../../../tests/test_data/air_temp.nc"

# Read selected variable(s) of interest.
# Use read_cube parameters to control edge trim selection.
cube = cset_read.read_cubes(
    file_path,
    ["temperature_at_screen_level"],
    subarea_type="gridcells",
    subarea_extent=[3, 2, 3, 1],
)[0]

# Plot single example frame using spatial_contour_plot
cset_plot.spatial_contour_plot(cube[-1])
