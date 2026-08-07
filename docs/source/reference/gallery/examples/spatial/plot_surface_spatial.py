"""
Regional spatial plot
=====================

Generate spatial map of a 2D field (regional data example).

.. admonition:: References

   General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``generic_surface_spatial_plot_sequence.yaml``

   The following CSET operators are used:

   * :py:mod:`CSET.operators.read.read_cubes`
   * :py:mod:`CSET.operators.plot.spatial_pcolormesh_plot` or :py:mod:`CSET.operators.plot.spatial_contour_plot`.

Using *cset bake* on the command line
-------------------------------------

* Access recipe file using ``cset cookbook``.
* Set required recipe inputs on command line (or as environment variables for greater flexibility).
* Example to generate full-domain spatial maps of ``VARNAME`` for all output times::

    cset cookbook generic_surface_spatial_plot_sequence.yaml
    cset -v bake -i "input_data_path" -o "my_output_path" \\
                 -r generic_surface_spatial_plot_sequence.yaml \\
                 --VARNAME="temperature_at_screen_level" \\
                 --MODEL_NAME="my_model_label" \\
                 --METHOD="" \\
                 --SUBAREA_TYPE='None' --SUBAREA_EXTENT='None' --SUBAREA_NAME='None'

Configuring the *cset_workflow*
-------------------------------

* Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
* Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
* Set required configuration options on ``Diagnostics / Surface (2D) fields`` panel::

    SURFACE_FIELDS = ['temperature_at_screen_level', ...]
    SPATIAL_SURFACE_FIELD = True

Example python code
-------------------
"""

from CSET import sample_data_path
from CSET.operators import plot, read

# Set path to input data
filename = sample_data_path("air_temperature.nc")

# Read selected variable(s) of interest
cube = read.read_cube(filename, ["temperature_at_screen_level"])

# Plot single time using spatial_contour_plot
plot.spatial_contour_plot(cube[-1])
