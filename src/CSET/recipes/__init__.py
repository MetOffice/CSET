# © Crown copyright, Met Office (2022-2025) and CSET contributors.
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
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

from CSET._common import parse_recipe, slugify
from CSET.cset_workflow.lib.python.jinja_utils import get_models as get_models

logger = logging.getLogger(__name__)


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
    recipe_name: str | None = None, input_dir: Path | None = None
) -> Iterable[Path]:
    """Yield recipe file Paths matching the recipe name."""
    if recipe_name is None:
        recipe_name = ""
    if input_dir is None:
        input_dir = _version_agnostic_importlib_resources_file()
    for file in input_dir.iterdir():
        logger.debug("Testing %s", file)
        if recipe_name in file.name and file.is_file() and file.suffix == ".yaml":
            yield file
        elif file.is_dir() and file.name[0] != "_":  # Excludes __pycache__
            yield from _recipe_files_in_tree(recipe_name, file)


def _get_recipe_file(recipe_name: str, input_dir: Path | None = None) -> Path:
    """Return a Path to the recipe file."""
    if input_dir is None:
        input_dir = _version_agnostic_importlib_resources_file()
    file = input_dir / recipe_name
    logger.debug("Getting recipe: %s", file)
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
    logger.debug("Saving recipe to %s", output_file)
    if output_file.exists():
        logger.info("%s already exists in target directory, skipping.", file.name)
        return
    logger.info("Unpacking %s to %s", file.name, output_file)
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
        with YAML(typ="safe", pure=True) as yaml:
            recipe = yaml.load(file)
        print(f"\n\t{file.name}\n\t{''.join('─' * len(file.name))}\n")
        print(recipe.get("description"))


class RawRecipe:
    """A recipe to be parbaked.

    Parameters
    ----------
    recipe: str
        Name of the recipe file.
    model_ids: int | list[int]
        Model IDs to set the input paths for. Matches the corresponding workflow
        model IDs.
    variables: dict[str, Any] aggregation: bool
        Recipe variables to be inserted into $VAR placeholders in the recipe.
    aggregation: bool
        Whether this is an aggregation recipe or just a single case.

    Returns
    -------
    RawRecipe
    """

    recipe: str
    model_ids: list[int]
    variables: dict[str, Any]
    aggregation: bool

    def __init__(
        self,
        recipe: str,
        model_ids: int | list[int],
        variables: dict[str, Any],
        aggregation: bool,
    ) -> None:
        self.recipe = recipe
        self.model_ids = model_ids if isinstance(model_ids, list) else [model_ids]
        self.variables = variables
        self.aggregation = aggregation

    def __str__(self) -> str:
        """Return str(self).

        Examples
        --------
        >>> print(raw_recipe)
        generic_surface_spatial_plot_sequence.yaml (model 1)
            VARNAME        air_temperature
            MODEL_NAME     Model A
            METHOD         SEQ
            SUBAREA_TYPE   None
            SUBAREA_EXTENT None
        """
        recipe = self.recipe if self.recipe else "<unknown>"
        plural = "s" if len(self.model_ids) > 1 else ""
        ids = " ".join(str(m) for m in self.model_ids)
        aggregation = ", Aggregation" if self.aggregation else ""
        pad = max([0] + [len(k) for k in self.variables.keys()])
        variables = "".join(f"\n\t{k:<{pad}} {v}" for k, v in self.variables.items())
        return f"{recipe} (model{plural} {ids}{aggregation}){variables}"

    def __eq__(self, value: object) -> bool:
        """Return self==value."""
        if isinstance(value, self.__class__):
            return (
                self.recipe == value.recipe
                and self.model_ids == value.model_ids
                and self.variables == value.variables
                and self.aggregation == value.aggregation
            )
        return NotImplemented

    def parbake(self, ROSE_DATAC: Path, SHARE_DIR: Path) -> None:
        """Pre-process recipe to bake in all variables.

        Parameters
        ----------
        ROSE_DATAC: Path
            Workflow shared per-cycle data location.
        SHARE_DIR: Path
            Workflow shared data location.
        """
        # Ready recipe file to disk.
        subprocess.run(["cset", "-v", "cookbook", self.recipe], check=True)

        # Collect configuration from environment.
        if self.aggregation:
            # Construct the location for the recipe.
            recipe_dir = ROSE_DATAC / "aggregation_recipes"
            # Construct the input data directories for the cycle.
            data_dirs = [
                SHARE_DIR / f"cycle/*/data/{model_id}" for model_id in self.model_ids
            ]
        else:
            recipe_dir = ROSE_DATAC / "recipes"
            data_dirs = [ROSE_DATAC / f"data/{model_id}" for model_id in self.model_ids]

        # Ensure recipe dir exists.
        recipe_dir.mkdir(parents=True, exist_ok=True)

        # Add input paths to recipe variables.
        self.variables["INPUT_PATHS"] = data_dirs

        # Parbake this recipe, saving into recipe_dir.
        recipe = parse_recipe(Path(self.recipe), self.variables)
        output = recipe_dir / f"{slugify(recipe['title'])}.yaml"
        with open(output, "wt") as fp:
            with YAML(pure=True, output=fp) as yaml:
                yaml.dump(recipe)


class Config:
    """Namespace for easy access to configuration values.

    A namespace for easy access to configuration values (via config.variable),
    where undefined attributes return an empty list. An empty list evaluates to
    False in boolean contexts and can be safely iterated over, so it acts as an
    effective unset value.

    Parameters
    ----------
    config: dict
        Configuration key-value pairs.

    Example
    -------
    >>> conf = Config({"key": "value"})
    >>> conf.key
    'value'
    >>> conf.missing
    []
    """

    d: dict

    def __init__(self, config: dict) -> None:
        self.d = config

    def __getattr__(self, name: str):
        """Return an empty list for missing names."""
        return self.d.get(name, [])

    def asdict(self) -> dict:
        """Return config as a dictionary."""
        return self.d


def load_recipes(variables: dict[str, Any]) -> Iterable[RawRecipe]:
    """Load recipes enabled by configuration.

    Recipes are loaded using all loaders (python modules) in
    CSET.recipes.loaders. Each of these loaders must define a function with the
    signature `load(v: dict) -> Iterable[RawRecipe]`, which will be called with
    `variables`.

    A minimal example can be found in `CSET.recipes.loaders.test`.

    Parameters
    ----------
    variables: dict[str, Any]
        Workflow configuration from ROSE_SUITE_VARIABLES.

    Returns
    -------
    Iterable[RawRecipe]
        Configured recipes.

    Raises
    ------
    AttributeError
        When a loader doesn't provide a `load` function.
    """
    # Import here to avoid circular import.
    import CSET.recipes.loaders

    config = Config(variables)
    for loader in CSET.recipes.loaders.__all__:
        logger.info("Loading recipes from %s", loader)
        module = getattr(CSET.recipes.loaders, loader)
        yield from module.load(config)
