Point Observations
==================

METplus can work with point observations in several formats, with converters
available to MET's internal netcdf based format.

Point observation conversion happens in the ``metplus_ascii2nc`` task.  After
point observations have been converted they are used by ``metplus_point_stat``
to create statistics.


Site Information
----------------

BOM
~~~

Point observations primarily come from ODB2 files from production workflows.
These hold the QC'd observation data that gets fed into the DA system.

An embedded Python script in the ``metplus_ascii2nc`` task converts the ODB2
data into MET ASCII format.

The system that observations are loaded from can be set in ``rose-suite.conf`` with:
 * ``METPLUS_OBS_SYSTEM``: e.g. ``access_g4``, ``access_c3_dn``, ``custom``
 * ``CUSTOM_ODB2_PATTERN``: e.g. ``/path/to/file.odb2``

If ``METPLUS_OBS_SYSTEM="custom"`` ODB2 data will be read from
``CUSTOM_ODB2_PATTERN``, which can include strftime patterns to be replaced
with the valid time or METplus date placeholders.

The ODB2 fields are mapped to MET ASCII columns like:

.. csv-table:: ASCII Columns
    :header: "Index", "Field", "Description", "point_stat config"

    "0", "**Message_Type**", "uses `PrepBUFR names`_ where known, otherwise the ODB ``reportype@hdr`` value.","``POINT_STAT_MESSAGE_TYPE``"
    "1", "**Station_ID**", "``statid@hdr``"
    "2", "**Valid_Time**", "``date@hdr_time@hdr``"
    "3", "**Lat**", "``lat@hdr``"
    "4", "**Lon**", "``lon@hdr``"
    "5", "**Elevation**", "``stalt@hdr``"
    "6", "**Variable_Name**", "uses MET GRIB abbreviations","``OBS_VAR<n>_NAME``"
    "7", "**Level**", "is the observation pressure level (where available).","``OBS_VAR<n>_LEVELS=P<level>``"
    "8", "**Height**", "is the height above ground level.","``OBS_VAR<n>_LEVELS=Z0``"
    "9", "**QC_String**", "not currently used","``POINT_STAT_OBS_QUALITY_EXC``, ``POINT_STAT_OBS_QUALITY_INC``"
    "10", "**Observation_Value**", "``obsvalue@body``"

Basic QC is done on the ODB2 data before the conversion by
checking that ``report_status@hdr`` and ``datum_status@body`` are
both 1.

.. _PrepBUFR names: https://www.emc.ncep.noaa.gov/mmb/data_processing/prepbufr.doc/table_1.htm
