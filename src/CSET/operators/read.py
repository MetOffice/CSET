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

"""
Operators for reading various types of files from disk.
"""

from pathlib import Path

import iris
import iris.cube


def read_cubes(
    loadpath: Path, constraint: iris.Constraint = None, **kwargs
) -> iris.cube.CubeList:
    """
    Read operator that takes a path string (can include wildcards), and uses
    iris to load all the cubes matching stash and return a CubeList object.

    Arguments
    ---------
    loadpath: pathlike
        Path to where .pp/.nc files are located
    constraint: iris.Constraint or iris.ConstraintCombination, optional
        Constraints to filter by

    Returns
    -------
    cubes: iris.cube.CubeList
        Cubes extracted
    """

    if constraint:
        return iris.load(loadpath, constraint)
    else:
        return iris.load(loadpath)
