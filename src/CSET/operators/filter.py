"""
Operators to perform various kind of filtering.
"""
# This file probably wants renaming as it clashes with the builtin filter
# function.

import iris.cube


def filter_cubes(cubelist, stash, methodconstraint):

    """
    Arguments
    ---------

    * **cubelist**          - an iris.cube.CubeList containing cubes to iterate over.
    * **stash**             - an string containing the stash code to extract.
    * **methodconstraint**  - an tuple containining cube.cell_methods for filtering.

    Returns
    -------
    * **cube** - an iris.cube

    """

    # initialise empty cubelist to append filtered cubes too
    filtered_cubes = iris.cube.CubeList()

    # Iterate over all cubes and check stash/cell method
    # TODO - need to add additional filtering/checking i.e. time/accum, pressure level...
    for cube in cubelist:
        if cube.attributes['STASH'] == stash:
            if cube.cell_methods == methodconstraint:
                filtered_cubes.append(cube)

    # Check filtered cubes is a cubelist containing one cube.
    if len(filtered_cubes) == 1:
        return filtered_cubes[0]
    else:
        print('Still multiple cubes, additional filtering required...')
