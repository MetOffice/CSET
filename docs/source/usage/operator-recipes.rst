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

The recipes are text files written in `TOML`_, a configuration language that is
very similar to INI. They are saved with the ``.toml`` extension. Below is a
commented example recipe:

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
      [steps.args.constraint]
        # Can nest in another step to use its output as an argument.
        operator = "generate_constraints.generate_stash_constraints"
        # Input implicitly taken from the previous step, but can be overridden.
        input = "m01s03i236"

    [[steps]]
    operator = "write.write_cube_to_nc"
    [steps.args]
      # This is a magic value that becomes the runtime output file path.
      file_path = "MAGIC_OUTPUT_PATH"

There are a couple of subtle points to keep in mind. While the example above is
indented for clarity, indentation does not matter. The double square brackets
around ``[[steps]]`` are significant, as they mean that the steps are ordered
(specifically they are an `array of tables`_). The below code block shows how
you can nest multiple levels deep.

.. code-block:: toml

    [[steps]]
    operator = "filters.filter_cubes"
    [steps.args]
      [steps.args.constraint]
          operator = "constraints.combine_constraints"
          [steps.args.constraint.args.constraint1]
            operator = "constraints.generate_stash_constraint"
            input = "m01s03i236"
          [steps.args.constraint.args.constraint2]
            operator = "constraints.generate_cell_methods_constraint"
            input = []

.. _TOML: https://toml.io/
.. _array of tables: https://toml.io/en/v1.0.0#array-of-tables
