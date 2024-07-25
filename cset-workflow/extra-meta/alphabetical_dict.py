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

"""Operators to deal with json files."""

import json


def alphabetical(input_colorbar_file, output_colorbar_file):
    """
    Re-order the json dictionary file.

    Read in a json dictionary file, sort the values so they are
    in alphabetical order and output to a new json dictionary file.
    """
    try:
        with open(input_colorbar_file, "rt", encoding="UTF-8") as fp:
            colorbar = json.load(fp)

            sorted_colorbar_list = sorted(colorbar.items())

            sorted_colorbar_dict = {}
            for key, value in sorted_colorbar_list:
                sorted_colorbar_dict[key] = value

            try:
                with open(output_colorbar_file, "w", encoding="UTF-8") as f:
                    json.dump(sorted_colorbar_dict, f, indent=4)

            except FileNotFoundError:
                print("Output file " + output_colorbar_file + " not found")

    except FileNotFoundError:
        print("Input file " + input_colorbar_file + " not found")


input_colorbar_file = "colorbar_dict.json"
output_colorbar_file = "colorbar_dict_alphabetical.json"

alphabetical(input_colorbar_file, output_colorbar_file)
