"""Module to contain field mappings for UM STASH codes to LFRic long names."""

""" ORIGINAL CODE AT source=svn://fcm1/cma.xm_svn/contrib/trunk/irislib. """
""" Please update the original code source as well as this file if changes required. """

# Set up UM STASH code to cube name mapping
#  Form of entry is <stashcode>: (<long_name>, <grid>)
STASH_TO_LFRIC = {
    "m01s00i002": ("eastward_wind_at_cell_centres", "face"),
    "m01s00i003": ("northward_wind_at_cell_centres", "face"),
    "m01s00i004": ("air_potential_temperature", "face"),
    "m01s00i010": ("specific_humidity", "face"),
    "m01s00i012": ("specific_cloud_ice", "face"),
    "m01s00i023": ("grid_surface_snow_amount", "face"),
    "m01s00i024": ("grid_surface_temperature", "face"),
    "m01s00i025": ("boundary_layer_depth", "face"),
    "m01s00i026": ("surface_roughness_length", "face"),
    "m01s00i030": ("land_binary_mask", "face"),
    "m01s00i031": ("sea_ice_area_fraction", "face"),
    "m01s00i033": ("surface_altitude", "face"),
    "m01s00i150": ("upward_air_velocity_at_cell_interfaces", "face"),
    "m01s00i254": ("specific_cloud_liquid_water", "face"),
    "m01s00i265": ("area_cloud_fraction", "face"),
    "m01s00i266": ("bulk_cloud_fraction", "face"),
    "m01s00i267": ("liquid_cloud_fraction", "face"),
    "m01s00i268": ("frozen_cloud_fraction", "face"),
    "m01s00i389": ("dry_air_density", "face"),
    "m01s00i391": ("vapour_mixing_ratio", "face"),
    "m01s00i392": ("cloud_liquid_mixing_ratio", "face"),
    "m01s00i393": ("cloud_ice_mixing_ratio", "face"),
    "m01s00i394": ("rain_mixing_ratio", "face"),
    "m01s00i395": ("graupel_mixing_ratio", "face"),
    "m01s00i396": ("snow_mixing_ratio", "face"),
    "m01s00i407": ("pressure_at_cell_centres", "face"),
    "m01s00i408": ("pressure_at_cell_interfaces", "face"),
    "m01s00i409": ("surface_air_pressure", "face"),
    "m01s01i140": ("cosine_of_the_solar_zenith_angle", "face"),
    "m01s01i141": ("sunlit_fraction_of_the_timestep", "face"),
    "m01s01i142": ("cosine_of_the_solar_zenith_angle_radiative_timestep", "face"),
    "m01s01i143": ("sunlit_fraction_of_the_timestep_radiative_timestep", "face"),
    "m01s01i161": ("temperature_increment_from_sw_radiation", "face"),
    "m01s01i201": ("surface_net_shortwave_flux_radiative_timestep", "face"),
    "m01s01i202": ("surface_net_shortwave_flux", "face"),
    "m01s01i205": ("toa_upward_shortwave_flux", "face"),
    "m01s01i207": ("toa_direct_shortwave_flux", "face"),
    "m01s01i208": ("toa_upward_shortwave_flux_radiative_timestep", "face"),
    "m01s01i209": ("toa_upward_clear_shortwave_flux_radiative_timestep", "face"),
    "m01s01i210": ("surface_downward_clear_shortwave_flux_radiative_timestep", "face"),
    "m01s01i211": ("surface_upward_clear_shortwave_flux_radiative_timestep", "face"),
    "m01s01i215": ("surface_direct_shortwave_flux_radiative_timestep", "face"),
    "m01s01i216": ("surface_diffuse_shortwave_flux_radiative_timestep", "face"),
    "m01s01i217": ("upward_shortwave_flux_radiative_timestep", "face"),
    "m01s01i218": ("downward_shortwave_flux_radiative_timestep", "face"),
    "m01s01i219": ("upward_clear_shortwave_flux_radiative_timestep", "face"),
    "m01s01i220": ("downward_clear_shortwave_flux_radiative_timestep", "face"),
    "m01s01i235": ("surface_downward_shortwave_flux_radiative_timestep", "face"),
    "m01s01i254": (
        "weighted_warm_cloud_top_effective_radius_radiative_timestep",
        "face",
    ),
    "m01s01i255": ("warm_cloud_top_weight_radiative_timestep", "face"),
    "m01s02i161": ("temperature_increment_from_lw_radiation", "face"),
    "m01s02i201": ("surface_net_longwave_flux_radiative_timestep", "face"),
    "m01s02i204": ("total_column_cloud_fraction_radiative_timestep", "face"),
    "m01s02i205": ("toa_upward_longwave_flux_radiative_timestep", "face"),
    "m01s02i206": ("toa_upward_clear_longwave_flux_radiative_timestep", "face"),
    "m01s02i207": ("surface_downward_longwave_flux_radiative_timestep", "face"),
    "m01s02i208": ("surface_downward_clear_longwave_flux_radiative_timestep", "face"),
    "m01s02i217": ("upward_longwave_flux_radiative_timestep", "face"),
    "m01s02i218": ("downward_longwave_flux_radiative_timestep", "face"),
    "m01s02i219": ("upward_clear_longwave_flux_radiative_timestep", "face"),
    "m01s02i220": ("downward_clear_longwave_flux_radiative_timestep", "face"),
    "m01s02i298": ("aerosol_optical_depth_in_visible_radiative_timestep", "face"),
    "m01s02i308": ("liquid_cloud_mmr_radiative_timestep", "face"),
    "m01s02i309": ("ice_cloud_mmr_radiative_timestep", "face"),
    "m01s02i312": ("liquid_cloud_fraction_radiative_timestep", "face"),
    "m01s02i313": ("ice_cloud_fraction_radiative_timestep", "face"),
    "m01s02i321": ("calipso_low_cloud_mask", "face"),
    "m01s02i322": ("calipso_mid_cloud_mask", "face"),
    "m01s02i323": ("calipso_high_cloud_mask", "face"),
    "m01s02i325": ("calipso_cf_40_lvls_mask", "face"),
    "m01s02i330": ("sunlit_mask", "face"),
    "m01s02i337": ("isccp_ctp_tau", "face"),
    "m01s02i341": ("calipso_total_backscatter", "face"),
    "m01s02i344": ("calipso_low_cloud", "face"),
    "m01s02i345": ("calipso_mid_cloud", "face"),
    "m01s02i346": ("calipso_high_cloud", "face"),
    "m01s02i370": ("calipso_cfad_sr_40_lvls", "face"),
    "m01s02i473": ("calipso_cf_40_lvls_liq", "face"),
    "m01s02i474": ("calipso_cf_40_lvls_ice", "face"),
    "m01s02i475": ("calipso_cf_40_lvls_undet", "face"),
    "m01s03i025": ("boundary_layer_depth", "face"),
    "m01s03i181": ("temperature_increment_from_bl_scheme", "face"),
    "m01s03i182": ("vapour_increment_from_bl_scheme", "face"),
    "m01s03i183": ("liquid_water_increment_from_bl_scheme", "face"),
    "m01s03i184": ("frozen_water_increment_from_bl_scheme", "face"),
    "m01s03i185": ("eastward_wind_increment_from_bl_scheme", "face"),
    "m01s03i186": ("northward_wind_increment_from_bl_scheme", "face"),
    "m01s03i187": ("upward_air_velocity_increment_from_bl_scheme", "face"),
    "m01s03i192": ("bulk_cloud_fraction_increment_from_bl_scheme", "face"),
    "m01s03i193": ("liquid_cloud_fraction_increment_from_bl_scheme", "face"),
    "m01s03i194": ("frozen_cloud_fraction_increment_from_bl_scheme", "face"),
    "m01s03i208": ("lowest_layer_bulk_richardson_number", "face"),
    "m01s03i217": ("grid_surface_upward_sensible_heat_flux", "face"),
    "m01s03i219": ("surface_eastward_wind_stress", "face"),
    "m01s03i220": ("surface_northward_wind_stress", "face"),
    "m01s03i223": ("grid_surface_moisture_flux", "face"),
    "m01s03i225": ("eastward_wind_at_10m", "face"),
    "m01s03i226": ("northward_wind_at_10m", "face"),
    "m01s03i227": ("wind_speed_at_10m", "face"),
    "m01s03i234": ("grid_surface_upward_latent_heat_flux", "face"),
    "m01s03i236": ("temperature_at_screen_level", "face"),
    "m01s03i237": ("specific_humidity_at_screen_level", "face"),
    "m01s03i245": ("relative_humidity_at_screen_level", "face"),
    "m01s03i247": ("visibility_excluding precipitation_at_screen_level", "face"),
    "m01s03i248": ("fog_fraction_at_screen_level", "face"),
    "m01s03i258": ("surface_snow_melt_heat_flux", "face"),
    "m01s03i261": ("gross_primary_productivity", "face"),
    "m01s03i281": ("visibility_including_precipitation_at_screen_level", "face"),
    "m01s03i296": ("water_evaporation_flux_from_soil", "face"),
    "m01s03i297": ("grid_water_evaporation_flux_from_canopy", "face"),
    "m01s03i298": ("grid_surface_snow_sublimation_rate", "face"),
    "m01s03i304": ("turbulent_mixing_height", "face"),
    "m01s03i305": ("stable_boundary_layer_indicator", "face"),
    "m01s03i306": ("stratocumulus_over_stable_boundary_layer_indicator", "face"),
    "m01s03i307": ("wellmixed_boundary_layer_indicator", "face"),
    "m01s03i308": (
        "decoupled_stratocumulus_not_over_cumulus_boundary_layer_indicator",
        "face",
    ),
    "m01s03i309": (
        "decoupled_stratocumulus_over_cumulus_boundary_layer_indicator",
        "face",
    ),
    "m01s03i310": ("cumulus_capped_boundary_layer_indicator", "face"),
    "m01s03i340": ("shear_driven_boundary_layer_indicator", "face"),
    "m01s03i365": ("neutral_eastward_wind_at_10m", "face"),
    "m01s03i366": ("neutral_northward_wind_at_10m", "face"),
    "m01s03i367": ("neutral_wind_speed_at_10m", "face"),
    "m01s03i395": ("land_area_fraction", "face"),
    "m01s03i662": ("net_primary_productivity", "face"),
    "m01s04i142": (
        "tendency_of_atmosphere_water_vapor_content_due_to_pc2_checks",
        "face",
    ),
    "m01s04i143": (
        "tendency_of_atmosphere_cloud_liquid_water_content_due_to_pc2_checks",
        "face",
    ),
    "m01s04i144": (
        "tendency_of_atmosphere_cloud_ice_water_content_due_to_pc2_checks",
        "face",
    ),
    "m01s04i152": (
        "tendency_of_cloud_amount_in_atmosphere_layer_due_to_pc2_checks",
        "face",
    ),
    "m01s04i153": (
        "tendency_of_liquid_cloud_amount_in_atmosphere_layer_due_to_pc2_checks",
        "face",
    ),
    "m01s04i154": (
        "tendency_of_frozen_cloud_amount_in_atmosphere_layer_due_to_pc2_checks",
        "face",
    ),
    "m01s04i181": ("temperature_increment_due_to_microphysics", "face"),
    "m01s04i182": ("water_vapour_mixing_ratio_increment_due_to_microphysics", "face"),
    "m01s04i183": ("cloud_liquid__mixing_ratio_increment_due_to_microphysics", "face"),
    "m01s04i184": ("cloud_ice_mixing_ratio_increment_due_to_microphysics", "face"),
    "m01s04i189": ("rain_mixing_ratio_increment_due_to_microphysics", "face"),
    "m01s04i190": ("snow_mixing_ratio_increment_due_to_microphysics", "face"),
    "m01s04i191": ("graupel_mixing_ratio_increment_due_to_microphysics", "face"),
    "m01s04i192": ("bulk_cloud_volume_increment_due_to_microphysics", "face"),
    "m01s04i193": ("liquid_cloud_volume_increment_due_to_microphysics", "face"),
    "m01s04i194": ("frozen_cloud_volume_increment_due_to_microphysics", "face"),
    "m01s04i201": ("surface_microphysical_rainfall_amount", "face"),
    "m01s04i202": ("surface_microphysical_snowfall_amount", "face"),
    "m01s04i203": ("surface_microphysical_rainfall_rate", "face"),
    "m01s04i204": ("surface_microphysical_snowfall_rate", "face"),
    "m01s05i161": ("temperature_increment_from_convection", "face"),
    "m01s05i162": ("water_vapour_increment_from_convection", "face"),
    "m01s05i163": ("cloud_liquid_water_increment_from_convection", "face"),
    "m01s05i164": ("cloud_ice_water_increment_from_convection", "face"),
    "m01s05i172": ("bulk_cloud_volume_increment_from_convection", "face"),
    "m01s05i173": ("liquid_cloud_volume_increment_from_convection", "face"),
    "m01s05i174": ("frozen_cloud_volume_increment_from_convection", "face"),
    "m01s05i182": (
        "tendency_of_atmosphere_water_vapor_content_due_to_pc2_conv_coupling",
        "face",
    ),
    "m01s05i183": (
        "tendency_of_atmosphere_cloud_liquid_water_content_due_to_pc2_conv_coupling",
        "face",
    ),
    "m01s05i184": (
        "tendency_of_atmosphere_cloud_ice_water_content_due_to_pc2_conv_coupling",
        "face",
    ),
    "m01s05i185": ("u_increment_from_convection", "face"),
    "m01s05i186": ("v_increment_from_convection", "face"),
    "m01s05i187": (
        "potential_temperature_increment_from_convection_excluding_shallow_convection",
        "face",
    ),
    "m01s05i188": (
        "water_vapour_increment_from_convection_excluding_shallow_convection",
        "face",
    ),
    "m01s05i192": (
        "tendency_of_cloud_amount_in_atmosphere_layer_due_to_pc2_conv_coupling",
        "face",
    ),
    "m01s05i193": (
        "tendency_of_liquid_cloud_amount_in_atmosphere_layer_due_to_pc2_conv_coupling",
        "face",
    ),
    "m01s05i194": (
        "tendency_of_frozen_cloud_amount_in_atmosphere_layer_due_to_pc2_conv_coupling",
        "face",
    ),
    "m01s05i201": ("surface_convective_rainfall_amount", "face"),
    "m01s05i202": ("surface_convective_snowfall_amount", "face"),
    "m01s05i205": ("surface_convective_rainfall_rate", "face"),
    "m01s05i206": ("surface_convective_snowfall_rate", "face"),
    "m01s05i207": ("pressure_at_convective_cloud_base", "face"),
    "m01s05i208": ("pressure_at_convective_cloud_top", "face"),
    "m01s05i212": ("convective_cloud_amount", "face"),
    "m01s05i214": ("surface_rainfall_rate", "face"),
    "m01s05i215": ("surface_snowfall_rate", "face"),
    "m01s05i216": ("precipitation_rate", "face"),
    "m01s05i226": ("surface_precipitation_amount", "face"),
    "m01s05i246": ("convection_upward_massflux_half_levs", "face"),
    "m01s05i250": ("convection_upward_massflux", "face"),
    "m01s05i251": ("convection_downward_massflux", "face"),
    "m01s05i267": ("deep_convection_cfl_limited", "face"),
    "m01s05i268": ("midlevel_convection_cfl_limited", "face"),
    "m01s05i269": ("frequency_of_deep_convection", "face"),
    "m01s05i270": ("frequency_of_shallow_convection", "face"),
    "m01s05i272": ("frequency_of_midlevel_convection", "face"),
    "m01s05i277": ("deep_convective_precipitation_rate", "face"),
    "m01s05i278": ("shallow_convective_precipitation_rate", "face"),
    "m01s05i279": ("midlevel_convection_precipitation_rate", "face"),
    "m01s06i101": ("spectral_gwd_eastward_wind_stress", "face"),
    "m01s06i102": ("spectral_gwd_southward_wind_stress", "face"),
    "m01s06i103": ("spectral_gwd_westward_wind_stress", "face"),
    "m01s06i104": ("spectral_gwd_northward_wind_stress", "face"),
    "m01s06i105": ("spectral_gravity_wave_drag_U_wind_tendency", "face"),
    "m01s06i106": ("spectral_gravity_wave_drag_V_wind_tendency", "face"),
    "m01s06i201": ("orographic_drag_U_wind_stress", "face"),
    "m01s06i202": ("orographic_drag_V_wind_stress", "face"),
    "m01s06i207": ("orographic_gravity_wave_drag_U_wind_tendency", "face"),
    "m01s06i208": ("orographic_gravity_wave_drag_V_wind_tendency", "face"),
    "m01s06i223": ("orographic_gravity_wave_drag_U_wind_stress", "face"),
    "m01s06i224": ("orographic_gravity_wave_drag_V_wind_stress", "face"),
    "m01s08i208": ("mass_content_of_water_in_soil", "face"),
    "m01s08i209": ("grid_canopy_water_amount", "face"),
    "m01s08i223": ("mass_content_of_water_in_soil_layer", "face"),
    "m01s08i225": ("soil_temperature", "face"),
    "m01s08i229": (
        "mass_fraction_of_unfrozen_water_in_saturated_soil_moisture",
        "face",
    ),
    "m01s08i230": ("mass_fraction_of_frozen_water_in_saturated_soil_moisture", "face"),
    "m01s08i231": ("grid_surface_snow_melt_flux", "face"),
    "m01s08i233": ("grid_canopy_throughfall_flux", "face"),
    "m01s08i234": ("surface_runoff_flux", "face"),
    "m01s08i235": ("subsurface_runoff_flux", "face"),
    "m01s09i202": ("maximum_combined_cloud_amount_below_111m_asl", "face"),
    "m01s09i203": ("maximum_combined_cloud_amount_between_111_and_1949m_asl", "face"),
    "m01s09i204": ("maximum_combined_cloud_amount_between_1949_and_5574m_asl", "face"),
    "m01s09i205": ("maximum_combined_cloud_amount_between_5574_and_13608m_asl", "face"),
    "m01s09i210": (
        "cloud_base_altitude_asl_combined_cloud_amount_greater_than_2p5_okta",
        "face",
    ),
    "m01s09i216": ("combined_cloud_amount_random_overlap", "face"),
    "m01s09i217": ("combined_cloud_amount_maximum_random_overlap", "face"),
    "m01s09i233": (
        "ceilometer_filtered_combined_cloud_amount_maximum_random_overlap",
        "face",
    ),
    "m01s10i185": ("eastward_wind_increment_from_solver", "face"),
    "m01s10i186": ("northward_wind_increment_from_solver", "face"),
    "m01s10i187": ("vertical_air_velocity_increment_from_solver", "face"),
    "m01s12i185": ("eastward_wind_increment_from_advection", "face"),
    "m01s12i186": ("northward_wind_increment_from_advection", "face"),
    "m01s12i187": ("vertical_air_velocity_increment_from_advection", "face"),
    "m01s12i192": ("bulk_cloud_fraction_increment_from_advection", "face"),
    "m01s12i193": ("liquid_cloud_fraction_increment_from_advection", "face"),
    "m01s12i194": ("frozen_cloud_fraction_increment_from_advection", "face"),
    "m01s12i195": ("vapour_increment_from_advection", "face"),
    "m01s12i196": ("liquid_water_increment_from_advection", "face"),
    "m01s12i197": ("frozen_water_increment_from_advection", "face"),
    "m01s15i201": ("zonal_wind_at_pressure_levels", "face"),
    "m01s15i202": ("meridional_wind_at_pressure_levels", "face"),
    "m01s15i242": ("vertical_wind_at_pressure_levels", "face"),
    "m01s16i004": ("air_temperature", "face"),
    "m01s16i162": (
        "tendency_of_atmosphere_water_vapor_content_due_to_pc2_initiation",
        "face",
    ),
    "m01s16i163": (
        "tendency_of_atmosphere_cloud_liquid_water_content_due_to_pc2_initiation",
        "face",
    ),
    "m01s16i164": (
        "tendency_of_atmosphere_cloud_ice_water_content_due_to_pc2_initiation",
        "face",
    ),
    "m01s16i172": (
        "tendency_of_cloud_amount_in_atmosphere_layer_due_to_pc2_initiation",
        "face",
    ),
    "m01s16i173": (
        "tendency_of_liquid_cloud_amount_in_atmosphere_layer_due_to_pc2_initiation",
        "face",
    ),
    "m01s16i174": (
        "tendency_of_frozen_cloud_amount_in_atmosphere_layer_due_to_pc2_initiation",
        "face",
    ),
    "m01s16i182": (
        "tendency_of_atmosphere_water_vapor_content_due_to_pc2_pressure_change",
        "face",
    ),
    "m01s16i183": (
        "tendency_of_atmosphere_cloud_liquid_water_content_due_to_pc2_pressure_change",
        "face",
    ),
    "m01s16i192": (
        "tendency_of_cloud_amount_in_atmosphere_layer_due_to_pc2_pressure_change",
        "face",
    ),
    "m01s16i193": (
        "tendency_of_liquid_cloud_amount_in_atmosphere_layer_due_to_pc2_pressure_change",
        "face",
    ),
    "m01s16i202": ("geopotential_height_at_pressure_levels", "face"),
    "m01s16i203": ("temperature_at_pressure_levels", "face"),
    "m01s16i204": ("relative_humidity_wrt_ice_at_pressure_levels", "face"),
    "m01s16i206": ("specific_cloud_condensate", "face"),
    "m01s16i207": ("specific_total_water", "face"),
    "m01s16i222": ("air_pressure_at_mean_sea_level", "face"),
    "m01s16i256": ("relative_humidity_wrt_water_at_pressure_levels", "face"),
    "m01s30i112": ("wbig_eq_1_where_wphysics_gt_1", "face"),
    "m01s30i113": ("relative_humidity_over_ice_below_freezing", "face"),
    "m01s30i185": ("total_eastward_wind_increment", "face"),
    "m01s30i186": ("total_northward_wind_increment", "face"),
    "m01s30i187": ("total_vertical_air_velocity_increment", "face"),
    "m01s30i195": ("total_vapour_increment", "face"),
    "m01s30i196": ("total_liquid_water_increment", "face"),
    "m01s30i197": ("total_frozen_water_increment", "face"),
    "m01s30i201": ("zonal_wind_at_pressure_levels_for_climate_averaging", "face"),
    "m01s30i202": ("meridional_wind_at_pressure_levels_for_climate_averaging", "face"),
    "m01s30i203": ("vertical_wind_at_pressure_levels_for_climate_averaging", "face"),
    "m01s30i204": ("temperature_at_pressure_levels_for_climate_averaging", "face"),
    "m01s30i205": (
        "vapour_specific_humidity_at_pressure_levels_for_climate_averaging",
        "face",
    ),
    "m01s30i206": (
        "relative_humidity_wrt_ice_at_pressure_levels_for_climate_averaging",
        "face",
    ),
    "m01s30i207": (
        "geopotential_height_at_pressure_levels_for_climate_averaging",
        "face",
    ),
    "m01s30i208": ("omega_at_pressure_levels_for_climate_averaging", "face"),
    "m01s30i211": ("square_of_eastward_wind", "face"),
    "m01s30i212": ("product_of_eastward_wind_and_northward_wind", "face"),
    "m01s30i213": ("product_of_eastward_wind_and_upward_air_velocity", "face"),
    "m01s30i214": ("product_of_eastward_wind_and_air_temperature", "face"),
    "m01s30i215": ("product_of_eastward_wind_and_specific_humidity", "face"),
    "m01s30i217": ("product_of_eastward_wind_and_geopotential_height", "face"),
    "m01s30i218": (
        "product_of_eastward_wind_and_lagrangian_tendency_of_air_pressure",
        "face",
    ),
    "m01s30i222": ("square_of_northward_wind", "face"),
    "m01s30i223": ("product_of_northward_wind_and_upward_air_velocity", "face"),
    "m01s30i224": ("product_of_northward_wind_and_air_temperature", "face"),
    "m01s30i225": ("product_of_northward_wind_and_specific_humidity", "face"),
    "m01s30i227": ("product_of_northward_wind_and_geopotential_height", "face"),
    "m01s30i228": (
        "product_of_northward_wind_and_lagrangian_tendency_of_air_pressure",
        "face",
    ),
    "m01s30i233": ("square_of_upward_air_velocity", "face"),
    "m01s30i234": ("product_of_upward_air_velocity_and_air_temperature", "face"),
    "m01s30i235": ("product_of_upward_air_velocity_and_specific_humidity", "face"),
    "m01s30i237": ("product_of_upward_air_velocity_and_geopotential_height", "face"),
    "m01s30i238": (
        "product_of_upward_air_velocity_and_lagrangian_tendency_of_air_pressure",
        "face",
    ),
    "m01s30i244": ("square_of_air_temperature", "face"),
    "m01s30i245": ("product_of_air_temperature_and_specific_humidity", "face"),
    "m01s30i247": ("product_of_air_temperature_and_geopotential_height", "face"),
    "m01s30i248": (
        "product_of_lagrangian_tendency_of_air_pressure_and_air_temperature",
        "face",
    ),
    "m01s30i255": ("square_of_specific_humidity", "face"),
    "m01s30i257": ("product_of_specific_humidity_and_geopotential_height", "face"),
    "m01s30i258": (
        "product_of_lagrangian_tendency_of_air_pressure_and_specific_humidity",
        "face",
    ),
    "m01s30i277": ("square_of_geopotential_height", "face"),
    "m01s30i278": (
        "product_of_lagrangian_tendency_of_air_pressure_and_geopotential_height",
        "face",
    ),
    "m01s30i288": ("square_of_lagrangian_tendency_of_air_pressure", "face"),
    "m01s30i301": ("heaviside_function_at_pressure_levels", "face"),
    "m01s30i402": ("atmosphere_kinetic_energy_content", "face"),
    "m01s30i403": ("atmosphere_mass_of_air_per_unit_area", "face"),
    "m01s30i404": ("atmosphere_wetplusdry_mass_per_unit_area", "face"),
    "m01s30i405": ("atmosphere_mass_content_of_cloud_liquid_water", "face"),
    "m01s30i406": ("atmosphere_mass_content_of_cloud_ice", "face"),
    "m01s30i419": ("energy_correction_rate", "face"),
    "m01s30i420": ("atmosphere_energy_content", "face"),
    "m01s30i421": ("atmosphere_potential_energy_content", "face"),
    "m01s30i455": ("vertical_vorticity_at_pressure_levels", "face"),
    "m01s30i461": ("atmosphere_mass_content_of_water_vapor", "face"),
    "m01s34i072": ("mass_fraction_of_sulfur_dioxide_in_air", "face"),
    "m01s34i101": ("nucleation_soluble_mode_number", "face"),
    "m01s34i102": ("nucleation_soluble_mode_h2so4_mmr", "face"),
    "m01s34i103": ("aitken_soluble_mode_number", "face"),
    "m01s34i104": ("aitken_soluble_mode_h2so4_mmr", "face"),
    "m01s34i105": ("aitken_soluble_mode_black_carbon_mmr", "face"),
    "m01s34i106": ("aitken_soluble_mode_organic_matter_mmr", "face"),
    "m01s34i107": ("accumulation_soluble_mode_number", "face"),
    "m01s34i108": ("accumulation_soluble_mode_h2so4_mmr", "face"),
    "m01s34i109": ("accumulation_soluble_mode_black_carbon_mmr", "face"),
    "m01s34i110": ("accumulation_soluble_mode_organic_matter_mmr", "face"),
    "m01s34i111": ("accumulation_soluble_mode_sea_salt_mmr", "face"),
    "m01s34i112": ("accumulation_soluble_mode_dust_mmr", "face"),
    "m01s34i113": ("coarse_soluble_mode_number", "face"),
    "m01s34i114": ("coarse_soluble_mode_h2so4_mmr", "face"),
    "m01s34i115": ("coarse_soluble_mode_black_carbon_mmr", "face"),
    "m01s34i116": ("coarse_soluble_mode_organic_matter_mmr", "face"),
    "m01s34i117": ("coarse_soluble_mode_sea_salt_mmr", "face"),
    "m01s34i118": ("coarse_soluble_mode_dust_mmr", "face"),
    "m01s34i119": ("aitken_insoluble_mode_number", "face"),
    "m01s34i120": ("aitken_insoluble_mode_black_carbon_mmr", "face"),
    "m01s34i121": ("aitken_insoluble_mode_organic_matter_mmr", "face"),
    "m01s34i122": ("accumulation_insoluble_mode_number", "face"),
    "m01s34i123": ("accumulation_insoluble_mode_dust_mmr", "face"),
    "m01s34i124": ("coarse_insoluble_mode_number", "face"),
    "m01s34i125": ("coarse_insoluble_mode_dust_mmr", "face"),
    "m01s34i126": ("nucleation_soluble_mode_organic_matter_mmr", "face"),
    "m01s34i150": ("ageofair", "face"),
    "m01s35i024": ("potential_temperature_increment_from_spt", "face"),
    "m01s35i025": ("vapour_increment_from_spt", "face"),
}
