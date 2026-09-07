"""
Trim edge gridcells
===================

Generate spatial map of a 2D field with specified number of grid cells at domain edges trimmed.

.. admonition:: References

   General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``generic_surface_spatial_plot_sequence.yaml``

   The following CSET operators are used:

   * :py:mod:`CSET.operators.read.read_cubes`
   * :py:mod:`CSET.operators.plot.spatial_pcolormesh_plot` or :py:mod:`CSET.operators.plot.spatial_contour_plot`.

Using *cset bake* on the command line
-------------------------------------

* See :doc:`/reference/gallery/generated/spatial/plot_surface_spatial` for general settings.
* Set ``SUBAREA_TYPE`` to ``gridcells`` and ``SUBAREA_EXTENT`` to select edge trim widths [lower, upper, left, right].
* Use ``SUBAREA_NAME`` to add a plot label if required, or leave blank.

Example to generate spatial maps of ``temperature_at_screen_level`` for a selected sub-area all output times::

    cset cookbook generic_surface_spatial_plot_sequence.yaml
    cset -v bake -i "/path/to/input/data" -o "./output_path" \\
                 -r generic_surface_spatial_plot_sequence.yaml \\
                 --VARNAME="temperature_at_screen_level" \\
                 --MODEL_NAME="my_model_label" \\
                 --METHOD="SEQ" \\
                 --SUBAREA_TYPE='gridcells' --SUBAREA_EXTENT='[3, 2, 3, 1]' --SUBAREA_NAME=''

Configuring the *cset_workflow*
-------------------------------

* Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
* Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
* Set ``SELECT_SUBAREA`` to ``True``, set ``SUBAREA_TYPE`` to ``gridcells`` and set ``SUBAREA_EXTENT`` and ``SUBAREA_NAME`` on panel ``Cycling and Model options``.
* Set other required configuration options on ``Diagnostics / Surface (2D) fields`` panel::

    SELECT_SUBAREA = True
    SPATIAL_SURFACE_FIELD = True
    SUBAREA_TYPE = 'gridcells'
    SUBAREA_EXTENT = [3, 2, 3, 1]
    SUBAREA_NAME = ''
    SURFACE_FIELDS = ["temperature_at_screen_level", ...]


Example python code
-------------------
"""

from CSET import sample_data_path
from CSET.operators import plot, read

# Set path to input data
filename = sample_data_path("air_temperature.nc")

# Read selected variable(s) of interest
cube = read.read_cube(
    filename,
    ["temperature_at_screen_level"],
    subarea_type="gridcells",
    subarea_extent=[3, 2, 3, 1],
)

# Plot single time using spatial_contour_plot
plot.spatial_contour_plot(cube[-1])
