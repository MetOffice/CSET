# Copyright 2022 Met Office and contributors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

VerPy_location = os.getenv("VERPY_LOCATION")
if not VerPy_location:
    sys.exit(1)
sys.path.append(VerPy_location)

# Replace prelude() function if required
import errno
import datetime
import warnings
import argparse
from VerPy.job import run
from VerPy.plottheme import get_theme
import VerPy.abv2data


def mkdir_p(path):
    """Makes a directory, mimicking mkdir -p behaviour."""
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def str2bool(string):
    """
    Converts the string "True" or "true" to boolean True, otherwise returns \
    False.
    """
    return string.lower() == "true"


def parse_args():
    """Parses and returns command line arguments."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description="Plotting basic verification statistics",
    )

    # Required arguments
    parser.add_argument(
        "--plot_dir", type=str, help="Output plot directory", dest="plot_dir"
    )
    parser.add_argument(
        "--start",
        type=lambda d: datetime.datetime.strptime(d, "%Y%m%d%H%M"),
        help=("Start date for verification statistics " "format YYYYmmddHHMM"),
        dest="start",
    )
    parser.add_argument(
        "--end",
        type=lambda d: datetime.datetime.strptime(d, "%Y%m%d%H%M"),
        help=("End date for verification statistics " "format YYYYmmddHHMM"),
        dest="end",
    )
    parser.add_argument(
        "--source",
        type=str,
        help="List of directories containing ARD files",
        dest="source",
    )
    parser.add_argument(
        "--expids", type=str, help=("Experiment IDs used in the ", " ARD file names.")
    )
    parser.add_argument(
        "--model_names", type=str, help="Names for models", dest="model_names"
    )
    parser.add_argument(
        "--case_studies",
        type=str2bool,
        default=True,
        help=(
            "Set to True to ensure only appropriate plot types "
            " for case studies are created."
        ),
        dest="cs",
    )

    # Optional arguments
    parser.add_argument(
        "--areas",
        default=2015,
        type=int,
        help="Areas to plot verification statistics over",
        dest="areas",
    )
    parser.add_argument(
        "--vts",
        nargs="+",
        default=range(0, 2400, 100),
        type=int,
        help="Valid times to plot statistics at.",
        dest="vts",
    )
    parser.add_argument(
        "--fcrs",
        nargs="+",
        type=int,
        default=range(0, 12000, 100),
        help="Desired forecast lead times to use for plotting.",
        dest="fcrs",
    )
    parser.add_argument(
        "--diurnal_fcrs",
        nargs="+",
        default=range(300, 12100, 300),
        type=int,
        help="Forecast lead times for producing diurnal plots",
        dest="diurnal_fcrs",
    )

    # Parse the arguments
    args = parser.parse_args()

    # Checking input argument values

    return args


def get_surf_components(base_options):
    """
    Generates a list of components based on the options provided.
    A 'component' is an options dictionary (to be passed to :func:`VerPy.job.run`).

    A user-provided dictionary should provide the following keys:

        * start
        * end
        * expids
        * source

    Any other keys (e.g. verbosity) will also be used, but these 4 must
    exist.

    :param base_options: A dictionary containing common options between
                         components
    :return list: A list of component tuples
    """
    # Validate user-options
    if not isinstance(base_options, dict):
        raise Exception(f"Expecting dictionary argument, got {type(base_options)}.")
    for key in ("start", "end", "expids", "source"):
        if key not in base_options:
            raise Exception(f'Expecting key "{key}".')

    components = [
        # Temperature
        {
            "stat": [2, 7051, 7752, 7053],
            "type": "cnt",
            "truth": 10000,
            "param": (16, 1, -1.0),
            "jobid": "Temp",
        },
    ]

    # Add common options
    for comp in components:
        comp.update(base_options)

    return components


def main():
    """
    Plot standard (traditional) verification statistics from the
    supplied Area Results Database (ARD) file.

    This module uses the supplied configuration to produce timeseries, forecast range series
    and diurnal cycle plots of traditional verification metrics for both continuous
    and categorical meteorological variables.
    For example, Mean Error, Root Mean Square Error, Equitable Threat Score (and other
    contingency table derived metrics)
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{now} Starting general statistics plots...")

    # Parse command line arguments
    args = parse_args()

    outputdir = args.plot_dir
    start = args.start
    end = args.end
    source = list(filter(None, args.source.split(",")))
    print(source)
    expids = list(filter(None, args.expids.split(",")))
    print(expids)
    names = list(filter(None, args.model_names.split(",")))
    print(names)
    cs = args.cs

    # Change output types for case study/trial
    if cs:
        outputs = ["fcrdiurnal", "fcrseries"]
    else:
        outputs = ["fcrdiurnal", "fcrseries", "timeseries"]

    # First continuous statistics
    stat_opts = {
        "system": "MET",
        "start": start,
        "end": end,
        "plotopts": ["1x1", "skip empty"],
        "expids": expids,
        "source": source,
        "names": names,
        "area": args.areas,
        "vts": args.vts,
        "fcrs": args.fcrs,
        "confopts": "stderr",
        "dataopts": "equalize",
    }

    # Creating plottheme which can cope with up to 120 lead times (worst case UKV scenario)
    theme = get_theme("split")
    theme["palette"]["markers"] = theme["palette"]["markers"] * 10
    theme["palette"]["markersize"] = theme["palette"]["markersize"] * 10
    theme["palette"]["linestyles"] = theme["palette"]["linestyles"] * 10
    theme["palette"]["linewidths"] = theme["palette"]["linewidths"] * 10

    for output in outputs:
        print(f"{now} Continuous statistics, output type {output}.")

        statsdir = os.path.join(outputdir, "CSET_Example")
        # Can this be improved/replaced now?
        mkdir_p(statsdir)

        # Surface components: construct dictionary and then plot
        components = get_surf_components(stat_opts)
        for comp in components:
            comp["output"] = output

        if output == "timeseries":
            for comp in components:
                comp["jobid"] += "TS"
                comp["diffopts"] = ["True", "split diff"]
                comp["plotopts"] = ["1x2", "skip empty"]
                if "TCA" in comp["param"]:
                    comp["fcrs"] = args.cloud_fcrs
                if cs:
                    comp["compare-on-plot"] = "fcrs"
                    comp["plottheme"] = theme

        if output == "fcrseries":
            for comp in components:
                comp["jobid"] += "FCR"
                comp["diffopts"] = ["True", "split diff"]
                comp["plotopts"] = ["2x2", "skip empty"]
                if "Wind" in comp["param"]:
                    comp["diffopts"] = "True"

        if output == "fcrdiurnal":
            for comp in components:
                comp["jobid"] += "Diurnal"
                comp["fcrs"] = args.diurnal_fcrs
                comp["plottheme"] = theme

        if output == "diurnal":
            for comp in components:
                comp["jobid"] += "Diurnal"
                comp["compare-on-plot"] = "fcrs"
                comp["plottheme"] = theme

        try:
            run(statsdir, components)
        except VerPy.abv2data.ABV2DataError as e:
            warnings.warn(e)

    # Set up links for web display
    print(f"{now} Finished plot_stats!")
    print(f"View at {outputdir:s}/CSET_Example")


if __name__ == "__main__":
    main()
