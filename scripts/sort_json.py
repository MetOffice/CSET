#! /usr/bin/env python3
# © Crown copyright, Met Office (2022-2024) and CSET contributors.
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

"""Sort a JSON file."""

import argparse
import hashlib
import json
import os
import sys


def sort_dict(d: dict) -> dict:
    """Recursively sort a dictionary."""
    # Thank you to https://stackoverflow.com/a/47882384
    return {k: sort_dict(v) if isinstance(v, dict) else v for k, v in sorted(d.items())}


def main():
    """Sort the keys in a JSON file, overwriting the original file."""
    parser = argparse.ArgumentParser(description="Sort a JSON file alphabetically.")
    parser.add_argument("input_file", type=str, help="JSON file to sort.")
    args = parser.parse_args()

    try:
        with open(args.input_file, "rt", encoding="UTF-8") as fp:
            data = json.load(fp)
    except FileNotFoundError:
        print(f"Input file {args.input_file} not found", file=sys.stderr)
        return 1
    except json.JSONDecodeError:
        print(f"Input file {args.input_file} is not valid JSON", file=sys.stderr)
        return 1

    if isinstance(data, dict):
        data = sort_dict(data)

    output_file = f".tmp-{args.input_file}-sorted.json".replace("/", "")
    with open(output_file, "wt", encoding="UTF-8") as fp:
        json.dump(data, fp, indent=2)
        # End file with a newline.
        fp.write("\n")

    # Check if sorting changed the file.
    with open(args.input_file, "rb") as fp:
        original_digest = hashlib.file_digest(fp, "sha256").digest()
    with open(output_file, "rb") as fp:
        new_digest = hashlib.file_digest(fp, "sha256").digest()

    if original_digest == new_digest:
        # File unchanged, don't overwrite and return zero.
        os.remove(output_file)
        return 0
    else:
        # File changed, overwrite and return non-zero.
        # Atomically replace original file via rename.
        os.rename(output_file, args.input_file)
        return 1


if __name__ == "__main__":
    sys.exit(main())
