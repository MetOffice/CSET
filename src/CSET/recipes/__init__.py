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

"""Operations on recipes."""

import importlib.resources
import logging
import sys
import warnings
from collections.abc import Iterable
from pathlib import Path

import ruamel.yaml


class FileExistsWarning(UserWarning):
    """Warning a file already exists, and some unusual action shall be taken."""


def _version_agnostic_importlib_resources_file() -> Path:
    """Transitional wrapper to importlib.resources.files().

    Importlib behaviour changed in 3.12 to avoid circular dependencies.
    """
    if sys.version_info.minor >= 12:
        input_dir = importlib.resources.files()
    else:
        import CSET.recipes

        input_dir = importlib.resources.files(CSET.recipes)
    return input_dir


def _recipe_files_in_tree(
    recipe_name: str = None, input_dir: Path = None
) -> Iterable[Path]:
    """Yield recipe file Paths matching the recipe name."""
    if recipe_name is None:
        recipe_name = ""
    if input_dir is None:
        input_dir = _version_agnostic_importlib_resources_file()
    for file in input_dir.iterdir():
        logging.debug("Testing %s", file)
        if recipe_name in file.name and file.is_file() and file.suffix == ".yaml":
            yield file
        elif file.is_dir() and file.name[0] != "_":  # Excludes __pycache__
            yield from _recipe_files_in_tree(recipe_name, file)


def _get_recipe_file(recipe_name: str, input_dir: Path = None) -> Path:
    """Return a Path to the recipe file."""
    if input_dir is None:
        input_dir = _version_agnostic_importlib_resources_file()
    file = input_dir / recipe_name
    logging.debug("Getting recipe: %s", file)
    if not file.is_file():
        raise FileNotFoundError("Recipe file does not exist.", recipe_name)
    return file


def unpack_recipe(recipe_dir: Path, recipe_name: str) -> None:
    """
    Unpacks recipes files into a directory, creating it if it doesn't exist.

    Parameters
    ----------
    recipe_dir: Path
        Path to a directory into which to unpack the recipe files.
    recipe_name: str
        Name of recipe to unpack.

    Raises
    ------
    FileExistsError
        If recipe_dir already exists, and is not a directory.

    OSError
        If recipe_dir cannot be created, such as insufficient permissions, or
        lack of space.
    """
    file = _get_recipe_file(recipe_name)
    recipe_dir.mkdir(parents=True, exist_ok=True)
    output_file = recipe_dir / file.name
    logging.debug("Saving recipe to %s", output_file)
    if output_file.exists():
        warnings.warn(
            f"{file.name} already exists in target directory, skipping.",
            FileExistsWarning,
            stacklevel=2,
        )
        return
    logging.info("Unpacking %s to %s", file.name, output_file)
    output_file.write_bytes(file.read_bytes())


def list_available_recipes() -> None:
    """List available recipes to stdout."""
    print("Available recipes:")
    for file in _recipe_files_in_tree():
        print(f"\t{file.name}")


def detail_recipe(recipe_name: str) -> None:
    """Detail the recipe to stdout.

    If multiple recipes match the given name they will all be displayed.

    Parameters
    ----------
    recipe_name: str
        Partial match for the recipe name.
    """
    for file in _recipe_files_in_tree(recipe_name):
        with ruamel.yaml.YAML(typ="safe", pure=True) as yaml:
            recipe = yaml.load(file)
        print(f"\n\t{file.name}\n\t{''.join('─' * len(file.name))}\n")
        print(recipe.get("description"))
