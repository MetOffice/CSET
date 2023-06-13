Operator Recipes
================

Operators individually don't form a complete task. Instead they need to be
chained together with *operator recipes*. A recipe is a config file that details
what operators to run, in what order, and with what extra arguments. Each recipe
forms a complete chain processing an input file and producing an output file.

Operator recipes can be run either with the ``cset operators`` command, or from
a python script.

.. code-block:: python

    import CSET.operators

    recipe = CSET.operators.RECIPES.extract_instant_air_temp
    CSET.operators.execute_recipe(recipe, "/input/file/path.nc", "/output/file/path.nc")

Recipe format
-------------

The recipes are text files written in `YAML 1.2`_, a configuration language that
is widely used. They are saved with the ``.yaml`` extension. Below is a
commented example recipe:

.. code-block:: yaml

    name: Name of recipe
    description: |
      Extended description that can
      go across multiple lines.

    steps:
      # Specify the operator to run in each step.
      - operator: read.read_cubes

    - operator: filters.filter_cubes
      # Can specify extra keyword arguments as sub-maps.
      constraint:
        # Can nest in another operator to use its output as an argument.
        operator: generate_constraints.generate_stash_constraints
        # Input implicitly taken from the previous step, but can be overridden
        # by using the appropriate keyword argument.
        stash: m01s03i236

    - operator: write.write_cube_to_nc
      # Specify the name of the argument, and its value.
      file_path: MAGIC_OUTPUT_PATH
      # "MAGIC_OUTPUT_PATH" is special and becomes the runtime output file path.

The name and description keys provide a human readable description of what the
recipe does. They are currently not used anywhere, but it is good practice to
include them for future users of the recipe.

The steps keys specifies a list of processing steps. The steps are run from top
to bottom, with each step specifying an operator to run, and optionally any
additional inputs to that operator. A step is denoted by a ``-`` under the
``steps:`` key. The operators are specified on the operator key. Its value
should be a string of the form ``file.function``. For additional inputs the key
should be the name of the argument.

The below code block shows how you can nest operators multiple levels deep. For
details of the specific operators involved, and the arguments that can take, see
the :doc:`/operators` page.

.. code-block:: yaml

  - operator: filters.filter_cubes
    constraint:
      operator: constraints.combine_constraints
      stash_constraint:
        operator: constraints.generate_stash_constraint
        stash: m01s03i236
      cell_methods_constraint:
        operator: constraints.generate_cell_methods_constraint
        cell_methods: []

.. _YAML 1.2: https://yaml.org/
