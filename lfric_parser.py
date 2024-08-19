import iris
import iris.cube

iris.FUTURE.datum_support = True
import datetime
import glob
import os
import re
import subprocess
import sys


def get_data(date, tmpdir):
    subprocess.check_output(
        [
            "/opt/moose-client-wrapper/bin/moo",
            "get",
            "moose:/devfc/u-dh663/field.nc.file/" + date + "_lfric_slam_umf_m_*.nc",
            tmpdir,
        ]
    )
    subprocess.check_output(
        [
            "/opt/moose-client-wrapper/bin/moo",
            "get",
            "moose:/devfc/u-dh663/field.nc.file/" + date + "_lfric_slam_s_*.nc",
            tmpdir,
        ]
    )


def check_var_meta(date, tmpdir):
    #    # MLEV LIST - CURRENTLY MISSING GEOPOT, WBPT, AND TEMPERATURE. Is m_r relative humidity??
    mlev_list = [
        "upward_air_velocity",
        "northward_wind",
        "eastward_wind",
        "potential_vorticity",
        "m_r",
        "combined_cloud_amount",
        "cloud_droplet_number_concentration",
        "m_v",
        "m_ci",
        "m_cl",
        "air_potential_temperature",
        "divergence_of_wind",
    ]

    for var in mlev_list:
        print("Working on", var)
        cubes = iris.load(tmpdir + date + "_lfric_slam_umf_m_???.nc", var)
        tmp_cubes = iris.cube.CubeList()
        for cube in cubes:
            data = cube.data
            lat = cube.coord("grid_latitude")
            lon = cube.coord("grid_longitude")
            ml = cube.coord("model_level_number")
            ml_dim = iris.coords.DimCoord(ml.points, standard_name="model_level_number")
            time = cube.coord("time")
            time_dim = iris.coords.DimCoord(
                time.points, standard_name="time", units=time.units
            )
            cube.remove_coord("time")
            new_cube = iris.cube.Cube(
                data,
                dim_coords_and_dims=[(time_dim, 0), (ml_dim, 1), (lat, 2), (lon, 3)],
                long_name=cube.name(),
                units=cube.units,
            )

            tmp_cubes.append(new_cube)

        if len(tmp_cubes.concatenate()) == 1:
            print(tmp_cubes.concatenate()[0])
            iris.save(
                tmp_cubes.concatenate()[0],
                tmpdir + "/" + date + "_" + var + "_MLEV_CUBES.nc",
            )
        else:
            print(tmp_cubes.concatenate())
            print(tmp_cubes.concatenate()[0])
            print(tmp_cubes.concatenate()[1])
            quit("Cant concat!!")

    filelist = glob.glob(tmpdir + date + "_lfric_slam_umf_m_???.nc")
    for f in filelist:
        print("deleting", f)
        os.remove(f)

    # Now, process surface level cubes
    clean_cubes = iris.cube.CubeList()

    # SURF LIST - CURRENTLY MISSING
    surf_list = [
        "air_pressure_at_mean_sea_level",
        "temperature_at_screen_level",
        "relative_humidity_at_screen_level",
        "eastward_wind_at_10m",
        "northward_wind_10m",
        "wind_speed_at_10m",
        "cloud_area_fraction",
        "surface_microphysical_precipitation_rate",
        "composite_radar_reflectivity",
        "visibility_including_precipitation_at_screen_level",
        "toa_upward_longwave_flux",
        "surface_net_shortwave_flux",
        "fog_fraction_at_screen_level",
        "radar_reflectivity_at_1km_above_the_surface",
        "dew_point_temperature_at_screen_level",
        "total_ice_water_path",
        "grid_surface_upward_latent_heat_flux",
        "surface_downward_longwave_flux",
        "atmosphere_mass_content_of_cloud_ice",
        "atmosphere_mass_content_of_water_vapor",
        "tropopause_level",
        "total_lightning_flash_rate",
        "surface_microphysical_graupelfall_rate",
        "cloud_base_altitude_asl_combined_cloud_amount_greater_than_2p5_okta",
        "grid_surface_temperature",
        "surface_downward_shortwave_flux",
        "grid_surface_snow_amount",
        "graupel_water_path",
        "turbulent_mixing_height",
        "toa_upward_shortwave_flux",
        "mass_content_of_water_in_soil",
        "surface_net_longwave_flux",
        "atmosphere_boundary_layer_thickness",
    ]

    for var in surf_list:
        print("Working on", var)
        cubes = iris.load(tmpdir + date + "_lfric_slam_s_???.nc", var)
        tmp_cubes = iris.cube.CubeList()
        for cube in cubes:
            data = cube.data
            if var == "surface_microphysical_precipitation_rate":
                data = data * 3600.0
                cube.units = "kg m-2 hr-1"
            lat = cube.coord("grid_latitude")
            lon = cube.coord("grid_longitude")
            time = cube.coord("time")
            time_dim = iris.coords.DimCoord(
                time.points, standard_name="time", units=time.units
            )
            cube.remove_coord("time")
            new_cube = iris.cube.Cube(
                data,
                dim_coords_and_dims=[(time_dim, 0), (lat, 1), (lon, 2)],
                long_name=cube.name(),
                units=cube.units,
            )

            tmp_cubes.append(new_cube)

        if len(tmp_cubes.concatenate()) == 1:
            clean_cubes.append(tmp_cubes.concatenate()[0])
        else:
            quit("Cant concat!!")

    print("Saving SURF")
    print(clean_cubes)
    iris.save(clean_cubes, tmpdir + "/" + date + "_SURF_CUBES.nc")

    filelist = glob.glob(tmpdir + date + "_lfric_slam_s_???.nc")
    for f in filelist:
        print("deleting", f)
        os.remove(f)


def update_var_in_file(file_path, variable_name, new_value):
    def process_line(line):
        # Regular expression to match the specific key-value pair
        match = re.match(rf"^({variable_name})=(.*)$", line.strip())
        if match:
            key, value = match.groups()
            value = new_value
            return f"{key}={value}"
        return line.strip()

    # Read the file
    with open(file_path, "r") as file:
        lines = file.readlines()

    # Process each line
    processed_lines = [process_line(line) for line in lines]

    # Write the changes back to the file
    with open(file_path, "w") as file:
        file.write("\n".join(processed_lines) + "\n")


casestudy_lookup = [
    [0, "20190725T0000Z", "UK001"],
    [1, "20191014T0000Z", "UK002"],
    [2, "20210213T0000Z", "UK003"],
    [3, "20220330T0000Z", "UK004"],
    [4, "20220616T0000Z", "UK005"],
    [5, "20220719T0000Z", "UK006"],
    [6, "20220817T0000Z", "UK007"],
    [7, "20220913T0000Z", "UK008"],
    [8, "20221011T0000Z", "UK009"],
    [9, "20221012T0000Z", "UK010"],
    [10, "20221102T0000Z", "UK011"],
    [11, "20221103T0000Z", "UK012"],
    [12, "20221107T0000Z", "UK013"],
    [13, "20221111T0000Z", "UK014"],
    [14, "20221129T0000Z", "UK015"],  # Missing data, known in Case study doc.
    [15, "20221209T0000Z", "UK016"],
    [16, "20221211T0000Z", "UK017"],
    [17, "20221215T0000Z", "UK018"],
    [18, "20221216T0000Z", "UK019"],
    [19, "20221218T0000Z", "UK020"],
    [20, "20230105T0000Z", "UK021"],
    [21, "20230117T0000Z", "UK022"],
    [22, "20230118T0000Z", "UK023 [NOT AVAILABLE]"],  # Seg Fault at TS 143
    [23, "20230121T0000Z", "UK024"],
    [24, "20230124T0000Z", "UK025 [NOT AVAILABLE]"],  # Failed needs re-running
    [25, "20230127T0000Z", "UK026 [NOT AVAILABLE]"],  # Same as above
    [26, "20230202T0000Z", "UK027"],
    [27, "20230203T0000Z", "UK028 [NOT AVAILABLE]"],
    [28, "20230207T0000Z", "UK029 [NOT AVAILABLE]"],
    [29, "20230210T0000Z", "UK030 [NOT AVAILABLE]"],
    [30, "20230313T0000Z", "UK031 [NOT AVAILABLE]"],
    [31, "20230214T0000Z", "UK032 [NOT AVAILABLE]"],
    [32, "20230216T0000Z", "UK033 [NOT AVAILABLE]"],
    [33, "20230225T0000Z", "UK034 [NOT AVAILABLE]"],
    [34, "20230307T0000Z", "UK035 [NOT AVAILABLE]"],
    [35, "20230308T0000Z", "UK036 [NOT AVAILABLE]"],
    [36, "20230313T0000Z", "UK037 [NOT AVAILABLE]"],
    [37, "20230314T0000Z", "UK038 [NOT AVAILABLE]"],
    [38, "20230325T0000Z", "UK039 [NOT AVAILABLE]"],
    [39, "20230331T0000Z", "UK040 [NOT AVAILABLE]"],
    [40, "20230511T0000Z", "UK041 [NOT AVAILABLE]"],
    [41, "20230513T0000Z", "UK042 [NOT AVAILABLE]"],
    [42, "20230518T0000Z", "UK043 [NOT AVAILABLE]"],
    [43, "20230521T0000Z", "UK044 [NOT AVAILABLE]"],
    [44, "20230524T0000Z", "UK045 [NOT AVAILABLE]"],
    [45, "20230527T0000Z", "UK046"],
    [46, "20230607T0000Z", "UK047"],
    [47, "20230610T0000Z", "UK048"],
    [48, "20230618T0000Z", "UK049"],
    [49, "20230621T0000Z", "UK050"],
    [50, "20230622T0000Z", "UK051"],
    [51, "20230628T0000Z", "UK052"],
    [52, "20230629T0000Z", "UK053"],
    [53, "20230703T0000Z", "UK054"],
    [54, "20230708T0000Z", "UK055"],
    [55, "20230709T0000Z", "UK056"],
    [56, "20230715T0000Z", "UK057"],
    [57, "20230912T0000Z", "UK058 [NOT AVAILABLE]"],
    [58, "20230928T0000Z", "UK059 [NOT AVAILABLE]"],
    [59, "20230926T0000Z", "UK060"],
    [60, "20231016T0000Z", "UK061"],
    [61, "20231101T0000Z", "UK062"],
    [62, "20231112T0000Z", "UK063"],
    [63, "20231209T0000Z", "UK064"],
    [64, "20231226T0000Z", "UK065 [NOT AVAILABLE]"],
    [65, "20240102T0000Z", "UK066"],
    [66, "20240121T0000Z", "UK067"],
    [67, "20240405T0000Z", "UK068"],
    [68, "20220101T0000Z", "UK20220101"],
    [69, "20220201T0000Z", "UK20220201"],
    [70, "20220301T0000Z", "UK20220301"],
    [71, "20220401T0000Z", "UK20220401"],
    [72, "20220501T0000Z", "UK20220501"],
    [73, "20220601T0000Z", "UK20220601"],
    [74, "20220701T0000Z", "UK20220701"],
    [75, "20220801T0000Z", "UK20220801"],
    [76, "20220901T0000Z", "UK20220901"],
    [77, "20221001T0000Z", "UK20221001"],
    [78, "20221101T0000Z", "UK20221101"],
    [79, "20221201T0000Z", "UK20221201"],
    [80, "20230101T0000Z", "UK20230101 [NOT AVAILABLE]"],
    [81, "20230201T0000Z", "UK20230201"],
    [82, "20230301T0000Z", "UK20230301"],
    [83, "20230401T0000Z", "UK20230401"],
    [84, "20230501T0000Z", "UK20230501"],
    [85, "20230601T0000Z", "UK20230601"],
    [86, "20230701T0000Z", "UK20230701"],
    [87, "20230801T0000Z", "UK20230801"],
    [88, "20230901T0000Z", "UK20230901"],
    [89, "20231001T0000Z", "UK20231001"],
    [90, "20231101T0000Z", "UK20231101 [NOT AVAILABLE]"],
    [91, "20231201T0000Z", "UK20231201"],
]


def main():
    print("")
    case_idx = int(sys.argv[1])
    date = casestudy_lookup[case_idx][1]
    caseid = casestudy_lookup[case_idx][2]
    print("Running parser script on case study", date)
    tmpdir = os.environ["SCRATCH"] + "/tmp_csetrun_" + date + "/"
    try:
        os.mkdir(tmpdir)
    except FileExistsError:
        print("Note; dir already exists")
        pass
    print("Getting mass data...")
    get_data(date, tmpdir)
    print("Checking var and metadata")
    check_var_meta(date, tmpdir)  # needs 15GB ram, takes 20 mins.
    print("Modifying rose-suite.conf")
    date_obj = datetime.datetime.strptime(date, "%Y%m%dT%H%MZ")
    conf_loc = "/home/h04/jawarner/CSET/cset-workflow/rose-suite.conf"
    update_var_in_file(
        conf_loc,
        "CSET_INITIAL_CYCLE_POINT",
        '"'
        + (date_obj + datetime.timedelta(seconds=60 * 60)).strftime("%Y-%m-%dT%H:%M:%S")
        + '"',
    )
    update_var_in_file(
        conf_loc,
        "CSET_FINAL_CYCLE_POINT",
        '"'
        + (date_obj + datetime.timedelta(seconds=48 * 60 * 60)).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        + '"',
    )
    update_var_in_file(
        conf_loc, "CSET_INPUT_FILE_PATH", '"' + tmpdir + "*CUBES.nc" + '"'
    )
    update_var_in_file(
        conf_loc,
        "WEB_DIR",
        '"'
        + "$HOME/public_html/CSET/LFRIC_CASESTUDIES/v0_u_dh663/inprogress/"
        + caseid
        + "_"
        + date
        + "/"
        + '"',
    )

    print("Running workflow")  # Around 30 mins to run with good queues.
    subprocess.check_output(
        ["/opt/ukmo/utils/bin/cylc", "vip", "/home/h04/jawarner/CSET/cset-workflow"]
    )


if __name__ == "__main__":
    main()
