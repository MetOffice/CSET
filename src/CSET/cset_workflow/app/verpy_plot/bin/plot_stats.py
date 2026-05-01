#!/usr/bin/env python

"""
Produce Verpy Plots.

Creates verpy options dictionaries from configuration files and environment vbles,
then runs verpy to create the plots
"""

import argparse
import os

import VerPy
import VerPy.conf2opts

parser = argparse.ArgumentParser(
    prog="verpy_plot",
    description="produce verpy plots from the metplus results database",
    epilog="Only intended to run as part of the verpy_plot app in cset_workflow",
)

parser.add_argument("--conf", action="append")
parser.add_argument("--outdir")
parser.add_argument("--start")
parser.add_argument("--end")
parser.add_argument("--expid")


args = parser.parse_args()

opts_dicts, scard_dict = VerPy.conf2opts.conf2opts(args.conf)

for options in opts_dicts:
    options["start"] = args.start
    options["end"] = args.end
    options["expid"] = args.expid
    options["source"] = (
        f"{os.getenv('TABLENAME')}@{os.getenv('DB_DIR')}/{os.getenv('DB_NAME')}"
    )
    print(f"Options Dictionary: {options}")
    VerPy.job.run(args.outdir, options)
    # TODO create a json metadata file in outdir
    json_filename = f"{args.outdir}/{options['jobid']}/meta.json"
    print(f"writing metadata to json file: {json_filename}")
    with open(json_filename, "w") as jf:
        jf.write("{\n")
        jf.write('"title": Metplus Point Stat plots\n')
        jf.write('"category": Metplus plots\n')
        jf.write("}")
