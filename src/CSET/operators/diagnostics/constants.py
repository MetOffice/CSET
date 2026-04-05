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

# Below constants are used in cell statistiscs
CELL_CONNECTIVITY = 2
M_IN_KM = 1000
HOUR_IN_SECONDS = 3600
MAX_TICK_OVERRIDE = 100000
COLOURS = {
    "brewer_paired": ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c',
                      '#fb9a99', '#e31a1c', '#fdbf6f', '#ff7f00',
                      '#cab2d6', '#6a3d9a', '#ffff99', '#b15928'],
    "brewer_set3": ['#8dd3c7', '#ffffb3', '#bebada', '#fb8072',
                    '#80b1d3', '#fdb462', '#b3de69', '#fccde5',
                    '#d9d9d9', '#bc80bd', '#ccebc5', '#ffed6f'],
    # List of distinctive colours from the ADAQ toolbox
    # See http://rawgit.com/pelson/7248780/raw/
    # 8e571ff02a02aeaacc021edfa7d899b5b0118ea8/colors.html for full list of
    # available names
    "adaq": ['k', 'r', 'b', 'g', 'orange', 'c', 'm',
             'lawngreen', 'slategrey', 'y', 'limegreen', 'purple',
             'lightgrey', 'indigo', 'darkblue', 'plum',
             'teal', 'violet', 'saddlebrown', 'lightpink']
    }
