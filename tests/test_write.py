from CSET.operators import write, read, filters
from secrets import token_hex
from pathlib import Path


def test_write_cube_to_nc():
    """Write cube and verify."""
    cubes = read.read_cubes("tests/test_data/air_temp.nc")
    cube = filters.filter_cubes(cubes, "m01s03i236", ())
    filename = Path(f"/tmp/{token_hex(4)}write_test_cube.nc")
    write.write_cube_to_nc(cube, filename)
    written_cube = read.read_cubes(filename)[0]
    assert written_cube == cube
    filename.unlink()
