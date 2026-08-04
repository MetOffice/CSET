echo Processing File: $1
#grib_ls -p typeOfLevel $1 | sort | uniq
echo isobaricInhPa
grib_copy -w typeOfLevel=isobaricInhPa $1 $1_extract_pl.grib2
grib_to_netcdf $1_extract_pl.grib2 -o $1_extract_pl.nc
rm $1_extract_pl.grib2
echo heightAboveGround
grib_copy -w typeOfLevel=heightAboveGround $1 $1_extract_ag.grib2
grib_to_netcdf $1_extract_ag.grib2 -o $1_extract_ag.nc
rm $1_extract_ag.grib2
echo surface
grib_copy -w typeOfLevel=surface $1 $1_extract_sf.grib2
grib_to_netcdf $1_extract_sf.grib2 -o $1_extract_sf.nc
rm $1_extract_sf.grib2
echo meanSea
grib_copy -w typeOfLevel=meanSea $1 $1_extract_ms.grib2
grib_to_netcdf $1_extract_ms.grib2 -o $1_extract_ms.nc
rm $1_extract_ms.grib2
echo entireAtmosphere
grib_copy -w typeOfLevel=entireAtmosphere $1 $1_extract_ea.grib2
grib_to_netcdf $1_extract_ea.grib2 -o $1_extract_ea.nc
rm $1_extract_ea.grib2

#0: unknown / (unknown)                 (realization: 50; latitude: 721; longitude: 1440)
#1: unknown / (unknown)                 (realization: 50; latitude: 721; longitude: 1440)
#X2: air_pressure / (Pa)                 (realization: 50; latitude: 721; longitude: 1440)
#X3: snowfall_flux / (kg m-2 s-1)        (realization: 50; latitude: 721; longitude: 1440)
#X4: surface_downwelling_longwave_flux_in_air / (W m-2) (realization: 50; latitude: 721; longitude: 1440)
#X5: surface_downwelling_shortwave_flux_in_air / (W m-2) (realization: 50; latitude: 721; longitude: 1440)
#X6: surface_temperature / (K)           (realization: 50; latitude: 721; longitude: 1440)

#Y0: Total Precipitation / (kg m**-2)    (time: 1; -- : 50; latitude: 721; longitude: 1440)
#1: Snowfall water equivalent / (kg m**-2) (time: 1; -- : 50; latitude: 721; longitude: 1440)
#2: Surface long-wave (thermal) radiation downwards / (J m**-2) (time: 1; -- : 50; latitude: 721; longitude: 1440)
#Y3: Runoff water equivalent (surface plus subsurface) / (kg m**-2) (time: 1; -- : 50; latitude: 721; longitude: 1440)
#4: Skin temperature / (K)              (time: 1; -- : 50; latitude: 721; longitude: 1440)
#5: surface_air_pressure / (Pa)         (time: 1; -- : 50; latitude: 721; longitude: 1440)
#6: surface_downwelling_shortwave_flux_in_air / (J m**-2) (time: 1; -- : 50; latitude: 721; longitude: 1440)