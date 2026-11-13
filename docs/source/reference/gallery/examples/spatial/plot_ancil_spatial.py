"""
Ancillary spatial plot
======================

Generate spatial map of a 2D field (ancillary file data example).

.. admonition:: References

   General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``generic_surface_spatial_plot_sequence.yaml``

   The following CSET operators are used:

   * :py:mod:`CSET.operators.read.read_cubes`
   * :py:mod:`CSET.operators.plot.spatial_pcolormesh_plot` or :py:mod:`CSET.operators.plot.spatial_contour_plot`.

Using *cset bake* on the command line
-------------------------------------

* CSET supports reading of ancillary file inputs, enabling any generic recipe to be applied to ancillary variables in addition to model outputs.
* Access recipe file using ``cset cookbook``.
* Set required recipe inputs on command line.

Example to generate full-domain spatial maps of ``surface_altitude``::

    cset cookbook generic_surface_spatial_plot_sequence.yaml
    cset -v bake -i "/path/to/input/data" -o "./output_path" \\
                 -r generic_surface_spatial_plot_sequence.yaml \\
                 --VARNAME="surface_altitude" \\
                 --MODEL_NAME="my_model_label" \\
                 --METHOD="" \\
                 --SUBAREA_TYPE='None' --SUBAREA_EXTENT='None' --SUBAREA_NAME=''

Configuring the *cset_workflow*
-------------------------------

* The workflow can be used to generate outputs by treating ancillary variables in the same way as any other ``Diagnostics / Surface (2D) fields`` outputs.
* See :doc:`/reference/gallery/generated/spatial/plot_surface_spatial` for general settings.

* For simplicity, an additional ``Ancillary fields`` tab is provided.
* Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
* Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
* Set required configuration options on ``Diagnostics / Surface (2D) fields`` panel::

    SURFACE_FIELDS = ["surface_altitude", ...]
    SPATIAL_SURFACE_FIELD = True

Example python code
-------------------
"""

from CSET import sample_data_path
from CSET.operators import plot, read

# Set path to input data
filename = sample_data_path("orography.nc")

# Read selected variable(s) of interest
cube = read.read_cube(filename, ["surface_altitude"])

# Plot single field using spatial_pcolormesh_plot
plot.spatial_pcolormesh_plot(cube)
