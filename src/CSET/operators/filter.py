"""
Operators to perform various kind of filtering.
"""
# This file probably wants renaming as it clashes with the builtin filter
# function.

import iris.cube


def filter_cubes(cubelist, stash, methodconstraint=None, levelconstraint=None):

    """
    Arguments
    ---------

    * **cubelist**          - an iris.cube.CubeList containing cubes to iterate over.
    * **stash**             - an string containing the stash code to extract.
    * **methodconstraint**  - optional, an iris.constraint.
    * **levelconstraint**   - optional, an iris.constraint.

    Returns
    -------
    * **cubes** - an iris.cube.CubeList 

    """

    # initialise empty cubelist to append filtered cubes too
    filtered_cubes = iris.cube.CubeList()

    # Iterate over all cubes
    for cube in cubelist:
        if cube.attributes['STASH'] == stash:
            filtered_cubes.append(cube)    

    #TODO - while okay for this example, we need to be able to futher filter
    #cubes by 'cell_methods', levels etc. Some stash will return multiple cubes
    #with different time processing. E.g. wind gust stash (m01s03i463) has a 
    #cell method (CellMethod(method='maximum', coord_names=('time',), intervals=('1 hour',), comments=()),)
    #We could base this around iris.constraints

    return filtered_cubes
