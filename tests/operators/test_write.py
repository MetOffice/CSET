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

"""Writing operator tests."""

from pathlib import Path

from CSET.operators import write


def test_write_cube(cube, tmp_working_dir: Path):
    """Write cube and verify it was written."""
    file_path = tmp_working_dir / "cube.nc"
    write.write_cube_to_nc(cube, file_path, overwrite=True)
    assert file_path.is_file()


def test_write_cube_default_filename(cube, tmp_working_dir):
    """Write cube without specifying a filename."""
    Path("meta.json").write_text("{}", encoding="UTF-8")
    write.write_cube_to_nc(cube, overwrite=True)
    assert Path.cwd().joinpath("untitled.nc").is_file()


def test_write_cube_skip_write(cube, tmp_working_dir):
    """Cube is not written when skip_write is configured."""
    Path("meta.json").write_text('{"skip_write": true}', encoding="UTF-8")
    returned = write.write_cube_to_nc(cube, "output.nc", overwrite=True)
    assert returned == cube
    assert not Path.cwd().joinpath("output.nc").is_file()
