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

import logging
from pathlib import Path
from typing import Union
import tempfile
from uuid import uuid4
import subprocess

from CSET._recipe_parsing import parse_recipe


def save_graph(
    recipe_file: Union[Path, str], save_path: Path = None, auto_open: bool = False
):
    """
    Draws out the graph of a recipe, and saves it to a file.

    Parameters
    ----------
    recipe_file: Path | str
        The recipe to be graphed.

    save_path: Path
        Path where to save the generated image. Defaults to a temporary file.

    auto_open: bool
        Whether to automatically open the graph with the default image viewer.
    """

    recipe = parse_recipe(recipe_file)
    logging.debug("Parsed recipe: %s", recipe)
    if not save_path:
        save_path = Path(f"{tempfile.gettempdir()}/{uuid4()}.svg")
    logging.info("Saving graph to %s", save_path)

    # Placeholder of graph making while work in progress. This should be
    # replaced by usage of pygraphvis to generate an SVG.
    save_path.write_text(str(recipe["steps"]), "utf-8")

    if auto_open:
        # Stderr is redirected here to suppress gvfs-open deprecation warning.
        # See https://bugs.python.org/issue30219 for an example.
        subprocess.run(
            ("xdg-open", str(save_path)), check=True, stderr=subprocess.DEVNULL
        )
