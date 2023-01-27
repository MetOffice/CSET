Operator Recipes
================

Operators individually don't form a complete task. Instead they need to be
chained together with *operator recipes*. A recipe is a config file that details
what operators to run, in what order, and with what extra arguments. Each recipe
forms a complete chain processing an input file and producing an output file.

Operator recipes can be run either from the command line with ``python3 -m
CSET.operators``, or from a python script.

.. code-block:: python

    import CSET.operators

    recipe = CSET.operators.RECIPES.extract_instant_air_temp
    CSET.operators.execute_recipe(recipe, "/input/file/path.nc", "/output/file/path.nc")

Recipe format
-------------

The recipes are written in `TOML`_, a configuration language that is very
similar to INI.

.. code-block:: toml

    name = "Name of recipe"
    description = """Extended description"""

    [[steps]]
    # Specify the operator to run in each step.
    operator = "read.read_cubes"

    [[steps]]
    operator = "filters.filter_cubes"
    [steps.args]  # Can specify extra keyword arguments in a sub-table.
      cell_methods = []  # Specify the name of the argument, and its value.
      [steps.args.stash]
        # Can nest in another step to use its output as an argument.
        operator = "generate_constraints.generate_stash_constraints"
        # Input implicitly taken from the previous step, but can be overridden.
        input = "m01s03i236"

    [[steps]]
    operator = "write.write_cube_to_nc"
    [steps.args]
      # This is a magic value that becomes the runtime output file path.
      file_path = "MAGIC_OUTPUT_PATH"


.. _TOML: https://toml.io/
