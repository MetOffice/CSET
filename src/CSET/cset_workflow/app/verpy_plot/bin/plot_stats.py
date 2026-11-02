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
    parser.add_argument("--image-meta-tag", action="store_true", help="Index with image-meta-tag")
    parser.add_argument("--metadata", type=json.loads, default={"title": "Metplus plots"})

    args = parser.parse_args()

    opts_dicts, scard_dict = VerPy.conf2opts.conf2opts(args.conf)

    metadata = args.metadata
    metadata["category"] = "Metplus Plot"

    for options in opts_dicts:
        options["start"] = args.start
        options["end"] = args.end
        options["expids"] = args.expids
        options["source"] = (
            f"{os.getenv('TABLENAME')}@{os.getenv('DB_DIR')}/{os.getenv('DB_NAME')}"
        )
        if args.image_meta_tag:
            options["metadata"] = "index"

        print(f"Options Dictionary: {options}")
        VerPy.job.run(args.outdir, options)

        if not args.image_meta_tag:
            # Create a json metadata file in outdir
            json_filename = f"{args.outdir}/{options['jobid']}/meta.json"
            print(f"writing metadata to json file: {json_filename}")
            metadata_dict = {'jobid': options['jobid'], **metadata}
            with open(json_filename, "w") as jf:
                json.dump(metadata_dict, jf, indent=2)

    if args.image_meta_tag:
        with open(f"{args.outdir}/meta.json", "wt") as jf:
            json.dump(metadata, jf, indent=2)


if __name__ == "__main__":
    main()
