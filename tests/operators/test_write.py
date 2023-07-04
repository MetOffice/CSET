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

from pathlib import Path
import tempfile
from uuid import uuid4
import os

from CSET.operators import write, read


def test_write_cube_to_nc_string():
    """Write cube to string path and verify."""
    cube = read.read_cubes("tests/test_data/air_temp.nc")[0]
    filename = f"{tempfile.gettempdir()}/{uuid4()}.nc"
    write.write_cube_to_nc(cube, filename)
    # Check that the cube was written correctly
    written_cube = read.read_cubes(filename)[0]
    assert written_cube == cube
    os.unlink(filename)


def test_write_cube_to_nc_path():
    """Write cube to Path and verify."""
    cube = read.read_cubes("tests/test_data/air_temp.nc")[0]
    filepath = Path(f"{tempfile.gettempdir()}/{uuid4()}.nc")
    write.write_cube_to_nc(cube, filepath)
    # Check that the cube was written correctly
    written_cube = read.read_cubes(filepath)[0]
    assert written_cube == cube
    filepath.unlink()
