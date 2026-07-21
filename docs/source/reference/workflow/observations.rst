Point Observations
==================

METplus can work with point observations in several formats, with converters
available to MET's internal netcdf based format.

Point observation conversion happens in the ``metplus_prep_obs`` and
``metplus_ascii2nc`` tasks.  After point observations have been converted they
are used by ``metplus_point_stat`` to create statistics.

ODB2
----

ODB2 format data is first converted to MET ASCII format and then
to MET point nc format. The ``pyodc`` library is required to do
this.

To enable generic ODB2 format conversion add the opt flag ``odb2`` to the task
``metplus_prep_obs``.

ODB2 data will be read from files matching
``$CUSTOM_ODB2_PATTERN``. This pattern can contain strftime-style
placeholders, which are replaced with the observation valid time,
and shell globs. ODB2 data with ``.gz``, ``.bz2`` or ``.zst``
extensions will be automatically decompressed before reading.

Valid times to read data can be set in ``$OBS_TIMES``. This should be an ISO time
recurrence pattern, e.g. ``R12/$CYLC_TASK_CYCLE_POINT/PT1H`` to read 12 times
one hour apart starting from the current cycle point. The Jinja2 filter
`duration_as`_ is useful when creating the recurrence.

The ODB2 fields are mapped to MET ASCII columns like:

.. csv-table:: ASCII Columns
    :header: "Index", "Field", "Description", "point_stat config"

    "0", "**Message_Type**", "uses `PrepBUFR names`_ where known, otherwise the ODB ``reportype@hdr`` value.","``POINT_STAT_MESSAGE_TYPE``"
    "1", "**Station_ID**", "``statid@hdr``"
    "2", "**Valid_Time**", "``date@hdr_time@hdr``"
    "3", "**Lat**", "``lat@hdr``"
    "4", "**Lon**", "``lon@hdr``"
    "5", "**Elevation**", "``stalt@hdr``"
    "6", "**Variable_Name**", "uses ODB variable names from https://codes.ecmwf.int/odb/varno/","``OBS_VAR<n>_NAME``"
    "7", "**Level**", "is the observation pressure level (where available).","``OBS_VAR<n>_LEVELS=P<level>``"
    "8", "**Height**", "is 0 for surface observations.","``OBS_VAR<n>_LEVELS=Z0``"
    "9", "**QC_String**", "not currently used","``POINT_STAT_OBS_QUALITY_EXC``, ``POINT_STAT_OBS_QUALITY_INC``"
    "10", "**Observation_Value**", "``obsvalue@body``"

Basic QC is done on the ODB2 data before the conversion by
checking that ``report_status@hdr`` and ``datum_status@body`` are
both 1.

A sample runtime for reading ODB2 format data is::

    [runtime]
        [[metplus_prep_fcst]]
            [[[environment]]]
                ROSE_APP_OPT_CONF_KEYS = "odb2"
                CUSTOM_ODB2_PATTERN = "/path/%Y%m%dT%H%MZ/obs.odb2.gz"
                {# Time separation between ODB2 files #}
                {% set ODB2_OBS_FREQ = "PT3H" %}
                {# Calculate the number of observations to read #}
                {% set ODB2_OBS_R = (
                        (ANALYSIS_LENGTH | duration_as('h')) /
                        (ODB2_OBS_FREQ | duration_as('h'))
                    ) | int
                %}
                OBS_TIMES = R{{ODB2_OBS_R}}/$CYLC_TASK_CYCLE_POINT/{{ODB2_OBS_FREQ}}


Customising ODB2 data at different sites
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If sites have a consistent path for their ODB2 data they can set
up preset patterns, see
``app/metplus_prep_fcst/bin/prepBureauNCI.py`` for an example.

.. _duration_as: https://cylc.github.io/cylc-doc/latest/html/user-guide/writing-workflows/jinja2.html#cylc.flow.jinja.filters.duration_as.duration_as
.. _PrepBUFR names: https://www.emc.ncep.noaa.gov/mmb/data_processing/prepbufr.doc/table_1.htm
