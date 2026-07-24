"""
Power spectra plot
==================

Generate power spectra of region-averaged field.

Line are generated using either CSET operators :py:mod:`CSET.operators.plot.plot_line_series`.

General functionality is provided using :doc:`CSET recipe </usage/operator-recipes>` ``generic_surface_power_spectrum_series.yaml``


A) Using *cset bake* on the command line
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Access recipe file using ``cset cookbook``.
- Set required recipe inputs on command-line (or as environment variables for greater flexibility).
- Use ``SINGLE_PLOT=True`` to generate one plot for all times.
- Use ``SINGLE_PLOT=False`` for a plot at each output time.
- Example to generate full-domain power spectra of ``VARNAME`` for all output times:

.. code-block::

    cset cookbook generic_surface_domain_mean_time_series
    cset bake -i "input_data_path" ["input_data_path2" "input_data_path3" "..."] -o "my_output_path"
              -r generic_surface_domain_mean_time_series
              --VARNAME="temperature_at_screen_level"
              --MODEL_NAME="my_model_label" "my_model_label2" "my_model_label3" "..."
              --SINGLE_PLOT="True"
              --SUBAREA_TYPE='None' --SUBAREA_EXTENT='None' --SUBAREA_NAME='None'
              [-s STYLE_FILE] [--plot-resolution PLOT_RESOLUTION] [--skip-write]


B) Configuring the *cset_workflow*
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Update workflow configuration settings via ``rose edit`` GUI or in ``rose-suite.conf`` file.
- Complete ``General setup options`` and ``Cycling and Model options`` details - see :doc:`/usage/workflow-configure`.
- Set required configuration options on ``Diagnostics / Surface (2D) fields`` panel.
- Set ``SPECTRUM_SURFACE_FIELD_SEQUENCE=False`` to generate spectrum for all times.
- Set ``SPECTRUM_SURFACE_FIELD_SEQUENCE=True`` for spectrum at each output time.

::

    SURFACE_FIELDS = ['temperature_at_screen_level', <other_variable_of_interest>, ...]
    SPECTRUM_SURFACE_FIELD = True
    SPECTRUM_SURFACE_FIELD_SEQUENCE = False


C) Example python code
^^^^^^^^^^^^^^^^^^^^^^
"""

import CSET.operators.plot as cset_plot
import CSET.operators.power_spectrum as cset_spectra
import CSET.operators.read as cset_read

# Set path to input data
file_paths = "../../../../../../tests/test_data/air_temperature_global.nc"

# Read selected variable(s) of interest
cubes = cset_read.read_cubes(file_paths, ["temperature_at_screen_level"])

# Compute domain power spectrum
spectra = cset_spectra.calculate_power_spectrum(cubes)

# Plot power spectrum as line plot
cset_plot.plot_line_series(
    spectra, series_coordinate="physical_wavenumber", single_plot=True
)
