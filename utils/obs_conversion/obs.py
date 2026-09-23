"""
Common column definitions for observation dataframes and station metadata.

Observations should provide at least these columns so they can be converted to MET format

Observations can include the station information directly in the observation dataframe or reference it through a separate station metadata dataframe.
"""

obs_dataframe_columns = [
    "prepbufr_type",
    "station_id",
    "valid",
    "var_name",
    "units",
    "level",
    "height",
    "QC",
    "value",
]

obs_station_columns = [
    "station_id",
    "latitude",
    "longitude",
    "elevation_asl",
]
