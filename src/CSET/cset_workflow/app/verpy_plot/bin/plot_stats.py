#!/usr/bin/env python

"""
Produce Verpy Plots.

Small utility to produce plots from METPlus results.
"""

import argparse
import json
import os
import os.path

import VerPy
import VerPy.conf2opts


def AddOdb2Names():
    from VerPy.parameter import get_param_by_code

    param = get_param_by_code(88,1,-1)
    param['short'].append('rh2m')


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

    args = parser.parse_args()

    AddOdb2Names()

    opts_dicts, scard_dict = VerPy.conf2opts.conf2opts(args.conf)

    for options in opts_dicts:
        options["start"] = args.start
        options["end"] = args.end
        options["expids"] = args.expids
        options["source"] = os.path.expandvars(options["source"])
        print(f"Options Dictionary: {options}")
        VerPy.job.run(args.outdir, options)

        # Create a json metadata file in outdir
        json_filename = f"{args.outdir}/{options['jobid']}/meta.json"
        print(f"writing metadata to json file: {json_filename}")
        metadata_dict = {
            "title": f"{options['system']} {options['type']} {options['output']}",
            "category": "Metplus plots",
        }
        with open(json_filename, "w") as jf:
            json.dump(metadata_dict, jf, indent=2)


if __name__ == "__main__":
    main()
