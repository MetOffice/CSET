from CSET.operators import read


def test_read_cubes():
    cubes = read.read_cubes("tests/test_data/air_temp.nc")
    assert len(cubes) == 3
    possible_cubes = [
        "<iris 'Cube' of air_temperature / (K) (time: 2; grid_latitude: 17; grid_longitude: 13)>",
        "<iris 'Cube' of air_temperature / (K) (time: 3; grid_latitude: 17; grid_longitude: 13)>",
    ]
    for cube in cubes:
        assert repr(cube) in possible_cubes
