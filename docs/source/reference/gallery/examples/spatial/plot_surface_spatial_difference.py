"""
Spatial difference plot
=======================

Generate spatial map of a 2D field difference (regional data example).

.. admonition:: References

   General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``surface_spatial_difference.yaml``

   The following CSET operators are used:

   * :py:mod:`CSET.operators.read.read_cubes`
   * :py:mod:`CSET.operators.misc.difference`
   * :py:mod:`CSET.operators.plot.spatial_pcolormesh_plot` or :py:mod:`CSET.operators.plot.spatial_contour_plot`.

Using *cset bake* on the command line
-------------------------------------

* Access recipe file using ``cset cookbook``.
* Set required recipe inputs on command line.

Example to generate full-domain spatial difference maps of ``temperature_at_screen_level`` between 2 input model files for all output times::

    cset cookbook surface_spatial_difference.yaml
    cset -v bake -i "/path/to/input/data_1" "/path/to/input/data_2" \\
                 -o "./output_path" \\
                 -r surface_spatial_difference.yaml \\
                 --VARNAME="temperature_at_screen_level" \\
                 --BASE_MODEL="my_model_1_label" \\
                 --OTHER_MODEL="my_model_2_label" \\
                 --METHOD="SEQ" \\
                 --SUBAREA_TYPE='None' --SUBAREA_EXTENT='None' --SUBAREA_NAME=''

Configuring the *cset_workflow*
-------------------------------

* Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
* Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
* Set required configuration options on ``Diagnostics / Surface (2D) fields`` panel::

    SURFACE_FIELDS = ["temperature_at_screen_level", ...]
    SPATIAL_DIFFERENCE_SURFACE_FIELD = True

Example python code
-------------------
"""

from CSET import sample_data_path
from CSET.operators import misc, plot, read

# Set path to input data
filename1 = sample_data_path("air_temperature_1.nc")
filename2 = sample_data_path("air_temperature_2.nc")

# Read selected variable(s) of interest
cubes = read.read_cubes([filename1, filename2], ["temperature_at_screen_level"])

# Compute difference between input cubes
diff = misc.difference(cubes)

# Plot single time using spatial_pcolormesh_plot
plot.spatial_pcolormesh_plot(diff[-1])
