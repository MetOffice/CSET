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

"""Visualise recipe into a graph."""

import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

import pygraphviz

from CSET._common import parse_recipe


def save_graph(
    recipe_file: Path | str,
    save_path: Path = None,
    auto_open: bool = False,
    detailed: bool = False,
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

    detailed: bool
        Whether to include operator arguments on the graph.

    Raises
    ------
    ValueError
        Recipe is invalid.
    """
    recipe = parse_recipe(recipe_file)
    if save_path is None:
        save_path = Path(f"{tempfile.gettempdir()}/{uuid4()}.svg")

    def step_parser(step: dict, prev_node: str) -> str:
        """Parse recipe to add nodes to graph and link them with edges."""
        logging.debug("Executing step: %s", step)
        node = str(uuid4())
        graph.add_node(node, label=step["operator"])
        kwargs = {}
        for key in step.keys():
            if isinstance(step[key], dict) and "operator" in step[key]:
                logging.debug("Recursing into argument: %s", key)
                sub_node = step_parser(step[key], prev_node)
                graph.add_edge(sub_node, node)
            elif key != "operator":
                kwargs[key] = step[key]
        graph.add_edge(prev_node, node)

        if detailed:
            graph.get_node(node).attr["label"] = f"{step['operator']}\n" + "".join(
                f"<{key}: {kwargs[key]}>\n" for key in kwargs
            )
        return node

    graph = pygraphviz.AGraph(directed=True)

    prev_node = "START"
    graph.add_node(prev_node)
    try:
        for step in recipe["steps"]:
            prev_node = step_parser(step, prev_node)
    except KeyError as err:
        raise ValueError("Invalid recipe") from err

    graph.draw(save_path, format="svg", prog="dot")
    print(f"Graph rendered to {save_path}")

    if auto_open:
        try:
            # Stderr is redirected here to suppress gvfs-open deprecation warning.
            # See https://bugs.python.org/issue30219 for an example.
            subprocess.run(
                ("xdg-open", str(save_path)), check=True, stderr=subprocess.DEVNULL
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Using print rather than logging as this is run interactively.
            print(
                "Cannot automatically display graph. Specify an output with -o instead.",
                file=sys.stderr,
            )
