from CSET.operators import read, filters


def test_filters_operator():
    cubes = read.read_cubes("tests/test_data/air_temp.nc")
    cube = filters.filter_cubes(cubes, "m01s03i236", ())
    assert cube.cell_methods == ()
    expected_cube = "<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>"
    assert repr(cube) == expected_cube
