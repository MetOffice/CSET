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

"""Operators for writing various types of files to disk."""

import secrets
from pathlib import Path

import iris
import iris.cube

from CSET._common import get_recipe_metadata, slugify


def write_cube_to_nc(
    cube: iris.cube.Cube | iris.cube.CubeList,
    filename: str = None,
    overwrite: bool = False,
    **kwargs,
) -> str:
    """Write a cube to a NetCDF file.

    This operator expects an iris cube object that will then be saved to disk.

    Arguments
    ---------
    cube: iris.cube.Cube | iris.cube.CubeList
        Data to save.
    filename: str, optional
        Path to save the cubes too. Defaults to the recipe title + .nc
    overwrite: bool, optional
        Whether to overwrite an existing file. If False the filename will have a
        unique suffix added. Defaults to False.

    Returns
    -------
    Cube | CubeList
        The inputted cube(list) (so further operations can be applied)
    """
    # Allow writing to be disabled without changing the recipe. This improves
    # runtime and avoids using excessive disk space for large runs.
    if get_recipe_metadata().get("skip_write"):
        return cube

    if filename is None:
        filename = slugify(get_recipe_metadata().get("title", "Untitled"))

    # Append a unique suffix if not overwriting. We use randomness rather than a
    # sequence number to avoid race conditions with multiple job runners.
    if not overwrite:
        filename = f"{filename}_{secrets.token_urlsafe(16)}.nc"

    # Ensure that output filename is a Path with a .nc suffix
    filename = Path(filename).with_suffix(".nc")
    # Save the file as nc compliant (iris should handle this)
    iris.save(cube, filename, zlib=True)
    return cube
