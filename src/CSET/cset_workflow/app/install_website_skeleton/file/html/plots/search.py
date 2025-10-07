#!/usr/bin/env python3

"""Interactive search utility to test the parser."""

import json
import sys

from parser import query2condition

if len(sys.argv) < 2:
    print("Usage: search.py FILE [QUERY]")
    sys.exit(1)

if len(sys.argv) == 2:
    query = input("Query: ")
else:
    query = " ".join(sys.argv[2:])

condition = query2condition(query)

with open(sys.argv[1], "rt") as file:
    for line in file:
        d = json.loads(line)
        if condition(d):
            print(d["title"])
