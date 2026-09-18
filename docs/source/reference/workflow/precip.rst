Precipitation Verification
--------------------------

Verification against precipitation observations can be enabled by setting::

    METPLUS_VERIFY_PRECIP=True

This enables precipitation verification, the exact statistics will vary by site
and which ``RUN_METPLUS`` settings are enabled for point, gridded or ensemble
verification.

You will also need to set the model variable name that contains precipitation,
the interval that the model precipitation is accumulated over and the
accumulation interval to output verification statistics for::

    METPLUS_PRECIP_VARIABLE="precipitation_flux"
    METPLUS_PRECIP_FCST_ACCUM="PT1H"
    METPLUS_PRECIP_VERIFY_ACCUM="PT1H"

This information is used by METplus recipes to select the forecast data. METplus recipes can use the variables::

    {ENV[METPLUS_PRECIP_FCST_VARIABLE]}   # As set in rose-suite.conf
    {ENV[METPLUS_PRECIP_FCST_ACCUM_H]}    # METPLUS_PRECIP_FCST_ACCUM converted to hours
    {ENV[METPLUS_PRECIP_VERIFY_ACCUM_H]}  # METPLUS_PRECIP_VERIFY_ACCUM converted to hours

BoM/NCI
=======

Verifying at NCI enables the following data sources:

* ADAM Station Obs (PointStat)
