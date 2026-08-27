#!/usr/bin/env bash
# Script for generating a minimal NetCDF file.
set -eu

outdir="$1"

# Create the output directory.
mkdir -p "${outdir}"

# Create a NetCDF file from a CDL definition.
ncgen -k nc4 -o "${outdir}/test.nc" << EOF
netcdf sample_data {
dimensions:
    lat = 2, lon = 2, time = 2;
variables:
    float lat(lat), lon(lon), time(time);
        lat:standard_name = "latitude";
        lon:standard_name = "longitude";
        time:standard_name = "time";
        time:units = "days since 2001-01-01";
    float t2m(time, lat, lon);
        t2m:standard_name = "air_temperature";
        t2m:units = "K";
data:
    time = 0, 1;
    lat = 0, 1;
    lon = 0, 1;
    t2m = 290, 290, 290, 290, 295, 295, 295, 295;
}
EOF
