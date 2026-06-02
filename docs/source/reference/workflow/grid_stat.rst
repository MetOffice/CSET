Comparing against Gridded Data
==============================

METplus can perform comparison against gridded datasets using the ``grid_stat``
tool. Enable ``grid_stat`` comparisons by adding to your ``rose-suite.conf``::

    RUN_METPLUS_GRID_STAT = True

Observations have to be configured for your site so that METplus knows the
correct source data paths.

Select which observations to run using e.g.::

    METPLUS_GRID_STAT_OBS = ["GPM"]

Output
------

The workflow creates spatial plots of the model field, observation field and
difference between model and observation. ``grid_stat`` handles regridding both
data sources to a common grid.

Observation Types
-----------------

GPM
^^^

https://gpm.nasa.gov/data/imerg

Compares model field ``stratiform_rainfall_flux`` against observation field
``precipitation_flux``.

Available sites:
* NCI
