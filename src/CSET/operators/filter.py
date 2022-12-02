"""
Operators to perform various kind of filtering.
"""
# This file probably wants renaming as it clashes with the builtin filter
# function.

import iris


def filter_cubes(
    cubelist: iris.cube.CubeList, stash: str, methodconstraint: tuple
) -> iris.cube:

    """
    Arguments
    ---------
    cubelist: iris.cube.CubeList
        Cubes to iterate over
    stash: str
        Stash code to extract
    methodconstraint: tuple
        cube.cell_methods for filtering

    Returns
    -------
    cube: iris.cube.Cube
        Single variable

    """

    # initialise empty cubelist to append filtered cubes too
    filtered_cubes = iris.cube.CubeList()

    # Initialise stash constraint
    stash_constraint = iris.AttributeConstraint(STASH=stash)

    # Iterate over all cubes and check stash/cell method
    # TODO - need to add additional filtering/checking i.e. time/accum, pressure level...
    for cube in cubelist.extract(stash_constraint):
        if cube.cell_methods == methodconstraint:
            filtered_cubes.append(cube)

    # Check filtered cubes is a cubelist containing one cube.
    if len(filtered_cubes) == 1:
        return filtered_cubes[0]
    else:
        print("Still multiple cubes, additional filtering required...")
