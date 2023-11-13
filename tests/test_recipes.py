# Copyright 2023 Met Office and contributors.
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

"""Recipe tests."""

from pathlib import Path

import pytest

import CSET.recipes


def test_unpack(tmp_path: Path):
    """Unpack directory containing sub-directories."""
    CSET.recipes._unpack_recipes_from_dir(Path("tests"), tmp_path)
    assert Path(tmp_path, "test_data/noop_recipe.yaml").exists()
    # Run again to check that warnings are produced when files collide.
    CSET.recipes._unpack_recipes_from_dir(Path("tests"), tmp_path)


def test_unpack_recipes_exception_collision(tmp_path: Path):
    """Output path already exists and is not a directory."""
    file_path = tmp_path / "regular_file"
    file_path.touch()
    with pytest.raises(FileExistsError):
        CSET.recipes.unpack_recipes(file_path)


def test_unpack_recipes_exception_permission():
    """Insufficient permission to create output directory.

    Will always fail if tests are run as root, but no one should be doing that,
    right?
    """
    with pytest.raises(OSError):
        CSET.recipes.unpack_recipes(Path("/usr/bin/cset"))
