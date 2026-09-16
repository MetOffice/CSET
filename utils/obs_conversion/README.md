# OBS Conversion

Convert various observation file formats to be compatible with MET and CSET

Different data formats are converted to a common DataFrame format, which can then be output to MET ASCII, MET NC, or Point NC formats to be read in by CSET.

## odb2_to_met

Converts ODB2 format observations to MET ASCII format

    odb2_to_met.py sample.odb2 --output sample.nc

The observations can then be used in MET's [point_stat](https://metplus.readthedocs.io/projects/met/en/latest/Users_Guide/point-stat.html) and [ensemble_stat](https://metplus.readthedocs.io/projects/met/en/latest/Users_Guide/ensemble-stat.html) tools to compare against gridded data, or put on a grid with [point2grid](https://metplus.readthedocs.io/projects/met/en/latest/Users_Guide/reformat_point.html#point2grid-tool)

### Requirements

 * [odc](https://anaconda.org/channels/conda-forge/packages/odc/overview)