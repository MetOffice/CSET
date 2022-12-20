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

from CSET.operators import write, read, filters
from secrets import token_hex
from pathlib import Path


def test_write_cube_to_nc():
    """Write cube to Path and string path and verify."""
    cubes = read.read_cubes("tests/test_data/air_temp.nc")
    cube = filters.filter_cubes(cubes, "m01s03i236", ())
    filename = f"/tmp/{token_hex(4)}_write_test_cube.nc"
    filepath = Path(f"/tmp/{token_hex(4)}_write_test_cube.nc")
    write.write_cube_to_nc(cube, filepath)
    write.write_cube_to_nc(cube, filename)
    written_cube = read.read_cubes(filepath)[0]
    assert written_cube == cube
    filepath.unlink()
    Path(filename).unlink()
