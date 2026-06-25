"""Python script to retrieve observations and serve to MET."""

import argparse
import datetime as dt

import pandas as pd

pd.options.mode.chained_assignment = None


# Converters
def dt_formatter(y, m, d, H, M):
    """Pandas formatter to convert datetime."""
    ob_dt = dt.datetime(int(y), int(m), int(d), hour=int(H), minute=int(M), second=0)
    return ob_dt.strftime("%Y%m%d_%H%M%S")


def t_converter(T_celsius):
    """Pandas formatter to convert temperature units."""
    T_kelvin = float(T_celsius) + 273.15
    return T_kelvin


# For RH converter apply the formula
# RH = 100 * exp(17.67Td / 243.5 + Td) / exp(17.67T / 243.5 +T)


# Retrieve function
def retrieve_vble(in_df, vble_name):
    """Extract and process a single variable from a multi-variable DataFrame."""
    try:
        out_name = vbles[vble_name]
        vdf = in_df[["SHID", "vld", "LAT", "LON", "ELEV", vble_name]]

        # rename column headers, retain good obs only and fill fixed values on required variables
        vdf.rename(
            columns={
                "SHID": "sid",
                "LAT": "lat",
                "LON": "lon",
                "ELEV": "elv",
                vble_name: "obs",
            },
            inplace=True,
        )

        vdf["typ"] = "ADPSFC"
        vdf["lvl"] = "s"
        vdf["hgt"] = -9999
        vdf["qc"] = "0"
        vdf["var"] = out_name

        # format the input 11-column observations:
        #   (1)  string:  Message_Type
        #   (2)  string:  Station_ID
        #   (3)  string:  Valid_Time(YYYYMMDD_HHMMSS)
        #   (4)  numeric: Lat(Deg North)
        #   (5)  numeric: Lon(Deg East)
        #   (6)  numeric: Elevation(msl)
        #   (7)  string:  Var_Name(or GRIB_Code)
        #   (8)  numeric: Level
        #   (9)  numeric: Height(msl or agl)
        #   (10) string:  QC_String
        #   (11) numeric: Observation_Value

        vdf = vdf.reindex(names, axis=1)
        vdf["sid"] = vdf["sid"].astype(str)

    except KeyError:
        print("Variable not defined in mapping dictionary, skipping variable")
        vdf = pd.DatFrame()

    return vdf


# Variables mapping #TODO: check and modify the mapping
vbles = {
    "TT": "TMP",
    "WDIR": "WD",
    "WSPD": "WS",
    "PMSL": "MSLP",
    "PRES": "P",
}

# Output columns
names = ["typ", "sid", "vld", "lat", "lon", "elv", "var", "lvl", "hgt", "qc", "obs"]

# Sorting arguments
parser = argparse.ArgumentParser(
    "Retrieve and filter obs from NCRMWF surface obs files"
)
parser.add_argument("input_file")
parser.add_argument("obs_datetime")
parser.add_argument("window_prev")
parser.add_argument("window_post")
args = parser.parse_args()

print(args)

obs_datetime = args.obs_datetime
window_prev = args.window_prev
window_post = args.window_post

# Arrange dates
ref_dt = dt.datetime(
    int(obs_datetime[0:4]),
    int(obs_datetime[4:6]),
    int(obs_datetime[6:8]),
    int(obs_datetime[9:11]),
    int(obs_datetime[11:13]),
    0,
)
obs_start = ref_dt + dt.timedelta(seconds=int(window_prev))
obs_start = obs_start.strftime("%Y%m%d_%H%M%S")
obs_end = ref_dt + dt.timedelta(seconds=int(window_post))
obs_end = obs_end.strftime("%Y%m%d_%H%M%S")

print(f"selecting obs between {obs_start} and {obs_end}")

# Processing
try:
    print(f"Input File:\t{args.input_file}")
    # Read and apply converters
    p1 = pd.read_csv(
        args.input_file,
        header=0,
        sep=r"\s+",
        quotechar="'",
        index_col="SEQN",
        converters={
            "TT": t_converter,
        },
    )
    p1["vld"] = pd.to_datetime(
        dict(
            year=p1["YR"],
            month=p1["MN"],
            day=p1["DY"],
            hour=p1["HR"],
            minute=p1["MI"],
        )
    ).dt.strftime("%Y%m%d_%H%M%S")
    p1.drop(["YR", "MN", "DY", "HR", "MI"], axis=1, inplace=True)

    all_dataframes = [retrieve_vble(p1, vble_name) for vble_name in vbles.keys()]

    p2 = pd.concat(all_dataframes).drop_duplicates(
        subset=["typ", "sid", "vld", "lat", "lon", "var", "lvl", "elv"], keep="last"
    )

    dated_p2 = p2[(p2["vld"] > obs_start) & (p2["vld"] <= obs_end)]

    # Non-valid observations carry the value -99.0
    valid_p2 = dated_p2[(dated_p2["obs"] != -99.0)]
    valid_p2 = valid_p2[(valid_p2["elv"] != -99.0)]
    print("out dataframe: " + repr(valid_p2))

    point_data = valid_p2.values.tolist()

    print(f"Data Length:\t{len(point_data)}")

except NameError:
    print("Can't find the input file... Or something else went wrong")
