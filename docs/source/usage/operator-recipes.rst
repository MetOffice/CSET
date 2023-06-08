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

The recipes are text files written in `YAML 1.2`_, a configuration language that is
similar to INI, but better defined. They are saved with the ``.toml`` extension.
Below is a commented example recipe:

.. code-block:: toml

    name = "Name of recipe"
    description = """Extended description"""

    [[steps]]
    # Specify the operator to run in each step.
    operator = "read.read_cubes"

    [[steps]]
    operator = "filters.filter_cubes"
    # Can specify extra keyword arguments in an args sub-table.
    [steps.args]
      [steps.args.constraint]
        # Can nest in another operator to use its output as an argument.
        operator = "generate_constraints.generate_stash_constraints"
        # Input implicitly taken from the previous step, but can be overridden.
        input = "m01s03i236"

    [[steps]]
    operator = "write.write_cube_to_nc"
    [steps.args]
      # Specify the name of the argument, and its value.
      file_path = "MAGIC_OUTPUT_PATH"
      # "MAGIC_OUTPUT_PATH" is special and becomes the runtime output file path.


There are a couple of subtle points to keep in mind. While the example above is
indented for clarity, indentation does not matter. The double square brackets
around ``[[steps]]`` are significant, as they mean that the steps are ordered
(specifically they are an `array of tables`_). The below code block shows how
you can nest operators multiple levels deep. For details of the specific
operators involved see the :doc:`/operators` page.

.. code-block:: toml

    [[steps]]
    operator = "filters.filter_cubes"
    [steps.args]
      [steps.args.constraint]
          operator = "constraints.combine_constraints"
          # Even the input override can be another operator.
          [steps.args.constraint.args.input]
            operator = "constraints.generate_stash_constraint"
            input = "m01s03i236"
          [steps.args.constraint.args.constraint1]
            operator = "constraints.generate_cell_methods_constraint"
            # Filtering for unprocessed value, i.e. no methods applied.
            input = []

.. _YAML 1.2: https://yaml.org/
.. _array of tables: https://toml.io/en/v1.0.0#array-of-tables
