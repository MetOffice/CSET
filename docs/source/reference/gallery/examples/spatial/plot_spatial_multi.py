"""
Overlay plots
=============

Generate spatial map with overlays of multiple 2D fields.

.. admonition:: References

   General functionality is provided using the following :doc:`CSET recipes </usage/operator-recipes>`:

   * ``multi_surface_spatial_plot_sequence.yaml`` for 3-layer plots (base layer, masked overlay layer, contour layer)
   * ``multi_overlay_spatial_plot_sequence.yaml`` for base-layer with masked pcolormesh overlay
   * ``multi_contour_spatial_plot_sequence.yaml`` for base-layer with contour overlay

   The following CSET operators are used:

   * :py:mod:`CSET.operators.read.read_cubes`
   * :py:mod:`CSET.operators.filters.generate_mask`
   * :py:mod:`CSET.operators.filters.apply_mask`
   * :py:mod:`CSET.operators.plot.spatial_multi_pcolormesh_plot`.

Using *cset bake* on the command line
-------------------------------------

* Access recipe file using ``cset cookbook``.
* Set required recipe inputs on command line.

Example to generate 3-layer full-domain spatial maps of ``temperature_at_screen_level``, with overlay of ``microphysical_surface_rainfall_rate`` masked to show only values greater than or equal to 0.05, and overlay of contours of ``air_pressure_at_sea_level`` for all output times::

    cset cookbook multi_surface_spatial_plot_sequence.yaml
    cset -v bake -i "/path/to/input/data" -o "./output_path" \\
                 -r multi_surface_spatial_plot_sequence.yaml \\
                 --VARNAME_BASE="temperature_at_screen_level" \\
                 --VARNAME_OVER="surface_microphysical_rainfall_rate" \\
                 --OVERLAY_MASK_CONDITION="ge" \\
                 --OVERLAY_MASK_VALUE="0.05" \\
                 --VARNAME_CONTOUR="air_pressure_at_mean_sea_level" \\
                 --MODEL_NAME="my_model_label" \\
                 --METHOD="SEQ" \\
                 --SUBAREA_TYPE='None' --SUBAREA_EXTENT='None' --SUBAREA_NAME='None'

Similar examples can be generated using recipe ``multi_overlay_spatial_plot_sequence.yaml`` for outputs with only ``VARNAME_BASE`` and ``VARNAME_OVER`` shown.

Alternatively, examples can be generated using recipe ``multi_contour_spatial_plot_sequence.yaml`` for outputs with only ``VARNAME_BASE`` and ``VARNAME_CONTOUR`` shown.


Configuring the *cset_workflow*
-------------------------------

* Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
* Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
* Set required configuration options on ``Diagnostics / Multi-variable plots`` panel
* A list of different variables can be specified as python lists to generate multiple different output plot combinations using the same workflow run.
* If all variables are set, 3-layer overlay plots are generated. If either ``OVERLAY`` or ``CONTOUR`` variables are not set, the relevant 2-layer outputs are generated.
::

    SPATIAL_MULTI_VARIABLE = True
    MULTI_BASE_FIELDS = ["temperature_at_screen_level", ...]
    MULTI_OVERLAY_FIELDS = ["surface_microphysical_rainfall_rate", ...]
    MULTI_OVERLAY_MASK_CONDITIONS = ["ge", ...]
    MULTI_OVERLAY_MASK_VALUES = ["0.05", ...]
    MULTI_CONTOUR_FIELDS = ["air_pressure_at_mean_sea_level", ...]
    SPATIAL_MULTI_FIELD_METHOD = ""


Example python code
-------------------
"""

from CSET import sample_data_path
from CSET.operators import plot, read

# Set path to input data
filename = sample_data_path("air_temperature_global.nc")

# Read selected variable(s) of interest
# Select sub-region to better illustrate output plot
cube = read.read_cube(
    filename,
    ["temperature_at_screen_level"],
    subarea_type="realworld",
    subarea_extent=[-40.0, 40.0, -120.0, -55.0],
)

# Plot single time using spatial_multi_pcolormesh_plot
# Here only contours of cube are shown for simplest illustration
# See operator documentation to generate more complex multi-layer examples
plot.spatial_multi_pcolormesh_plot(cube, contour_cube=cube)
