# Copyright 2022-2023 Met Office and contributors.
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
This module has an attribute for each recipe, holding the Path to that recipe.
"""

from pathlib import Path

try:
    from importlib.resources import files
except ImportError:
    # importlib has the files API from python 3.9
    from importlib_resources import files

import CSET.recipes

extract_instant_air_temp = files(CSET.recipes).joinpath("extract_instant_air_temp.yaml")


def unpack(recipe_dir: Path):
    """
    Unpacks recipes files into a directory, creating it if it doesn't exist.

    Parameters
    ----------
    recipe_dir: Path
        Path to a directory into which to unpack the recipe files.

    Raises
    ------
    FileExistsError
        If recipe_dir already exists, and is not a directory.

    OSError
        If recipe_dir cannot be created, such as insufficient permissions, or
        lack of space.
    """

    raise NotImplementedError

    recipe_dir.mkdir(parents=True, exist_ok=True)
    for file in files(CSET.recipes):
        # Loop over all recipes and write them to disk
        if file:  # Test file is a YAML one to avoid copying this code file.
            # Copy to recipe_dir
            pass
