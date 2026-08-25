"""
Select lat-lon subarea
======================

Generate spatial map of a 2D field over selected sub-region of data.

.. admonition:: References

   General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``generic_surface_spatial_plot_sequence.yaml``

   The following CSET operators are used:

   * :py:mod:`CSET.operators.read.read_cubes`
   * :py:mod:`CSET.operators.plot.spatial_pcolormesh_plot` or :py:mod:`CSET.operators.plot.spatial_contour_plot`.

Using *cset bake* on the command line
-------------------------------------

* See :doc:`/reference/gallery/generated/spatial/plot_surface_spatial` for general settings.
* Set ``SUBAREA_TYPE`` to ``realworld`` or ``modelrelative`` and ``SUBAREA_EXTENT`` to select edge trim widths [lower_lat, upper_lat, lower_lon, upper_lon].
* Use ``SUBAREA_NAME`` to add a plot label if required, or leave blank.

Example to generate spatial maps of ``temperature_at_screen_level`` for a selected sub-area all output times::

    cset cookbook generic_surface_spatial_plot_sequence.yaml
    cset -v bake -i "/path/to/input/data" -o "./output_path" \\
                 -r generic_surface_spatial_plot_sequence.yaml \\
                 --VARNAME="temperature_at_screen_level" \\
                 --MODEL_NAME="my_model_label" \\
                 --METHOD="SEQ" \\
                 --SUBAREA_TYPE='realworld' --SUBAREA_EXTENT='[-40.0, 40.0, -20.0, 55.0]' \\
                 --SUBAREA_NAME='Africa'

Configuring the *cset_workflow*
-------------------------------

* Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
* Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
* Set ``SELECT_SUBAREA`` to ``True``, choose ``SUBAREA_TYPE`` and set ``SUBAREA_EXTENT`` and ``SUBAREA_NAME`` on panel ``Cycling and Model options``.
* Set other required configuration options on ``Diagnostics / Surface (2D) fields`` panel::

    SELECT_SUBAREA = True
    SPATIAL_SURFACE_FIELD = True
    SUBAREA_TYPE = 'realworld'
    SUBAREA_EXTENT = [-40.0, 40.0, -20.0, 55.0]
    SUBAREA_NAME = 'Africa'
    SURFACE_FIELDS = ["temperature_at_screen_level", ...]


Example python code
-------------------
"""

from CSET import sample_data_path
from CSET.operators import plot, read

# Set path to input data
filename = sample_data_path("air_temperature_global.nc")

# Read selected variable(s) of interest
cube = read.read_cube(
    filename,
    ["temperature_at_screen_level"],
    subarea_type="realworld",
    subarea_extent=[-40.0, 40.0, -20.0, 55.0],
)

# Plot single time using spatial_contour_plot
plot.spatial_contour_plot(cube)
