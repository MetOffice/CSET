#!/usr/bin/env python

"""
Produce Verpy Plots.

Small utility to produce plots from METPlus results.
"""

import argparse
import json
import os

import VerPy
import VerPy.conf2opts


def setup_verpy():
    """Customise Verpy configs."""
    from VerPy.stats import MET_STAT_IDS, get_statistic

    # Compute errors from MPR, adapting SL1L2 partial sums
    me = get_statistic(stat=7051, system="MET", filetype="sl1l2")
    me["type"] = "mpr"
    me["requires"] = [10 - 6000, 10 - 4000]
    MET_STAT_IDS.append(me)


def main():
    """
    Produce Verpy Plots.

    Create verpy options dictionaries from configuration files and environment vbles.
    Run verpy to create the plots.
    """
    parser = argparse.ArgumentParser(
        prog="verpy_plot",
        description="produce verpy plots from the metplus results database",
        epilog="Only intended to run as part of the verpy_plot app in cset_workflow",
    )

    parser.add_argument("--conf", action="append", required=True)
    parser.add_argument("--outdir", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--expids", required=True, nargs="+")
    parser.add_argument(
        "--image-meta-tag", action="store_true", help="Index with image-meta-tag"
    )

    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    setup_verpy()

    opts_dicts, scard_dict = VerPy.conf2opts.conf2opts(args.conf)

    for options in opts_dicts:
        options["start"] = args.start
        options["end"] = args.end
        options["expids"] = args.expids

        if options["system"] == "MET":
            # Set up the database path for the current line type
            stream = options["type"]
            options["source"] = (
                f"{os.getenv('MET_TOOL')}_{stream}@{os.getenv('DB_DIR')}/{stream}.db"
            )

        if args.image_meta_tag:
            options["metadata"] = "index"

        print(f"Options Dictionary: {options}")
        VerPy.job.run(args.outdir, options)

        # Create a json metadata file in outdir
        json_filename = f"{args.outdir}/{options['jobid']}/meta.json"
        print(f"writing metadata to json file: {json_filename}")
        metadata_dict = {
            "title": "Metplus Point Stat plots",
            "category": "Metplus plots",
        }
        with open(json_filename, "w") as jf:
            json.dump(metadata_dict, jf, indent=2)

    if args.image_meta_tag:
        metadata_dict = {
            "title": "Metplus ImageMetaTag",
            "category": "Metplus plots",
        }
        with open(f"{args.outdir}/meta.json", "wt") as jf:
            json.dump(metadata_dict, jf, indent=2)


if __name__ == "__main__":
    main()
