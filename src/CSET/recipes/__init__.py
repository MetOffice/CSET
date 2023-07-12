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
import logging

try:
    from importlib.resources import files
except ImportError:
    # importlib has the files API from python 3.9
    from importlib_resources import files

import CSET.recipes as recipes


def _unpack_recipes_from_dir(input_dir: Path, output_dir: Path):
    """
    Loop over all recipes (excludes non-recipes) in input_dir and write them to
    output_dir.
    """
    for file in input_dir.iterdir():
        output_dir.mkdir(parents=True, exist_ok=True)
        if file.is_file() and file.suffix == ".yaml":
            if output_dir.joinpath(file.name).exists():
                logging.warning(
                    "%s already exists in target directory, skipping.", file.name
                )
            else:
                logging.info("Unpacking %s", file.name)
                output_dir.joinpath(file.name).write_bytes(file.read_bytes())
        elif file.is_dir() and file.name[0] != "_":  # Excludes __pycache__
            _unpack_recipes_from_dir(file, output_dir.joinpath(file.name))


def unpack_recipes(recipe_dir: Path):
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

    _unpack_recipes_from_dir(files(recipes), recipe_dir)
