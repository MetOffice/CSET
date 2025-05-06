Recipe Format
=============

The recipes are text files written in `YAML 1.2`_, a configuration language that
is widely used. They are saved with the ``.yaml`` extension.

Currently we develop separate recipes for similar diagnostics for Unified Model data and
LFRic data. Recipes are also separately developed for surface diagnostics and
diagnostics on vertical levels.

Below is a commented example recipe:

.. code-block:: yaml

  # Name of the recipe.
  title: Surface air temperature spatial plot
  # Category of recipe, used to group together multiple recipes in output.
  category: Quick look
  # Description will be displayed alongside output.
  description: |
    Extended description that can go across multiple lines. It is written in
    [Markdown](https://commonmark.org/help/) and can thus contain links and
    _formatting_.

  # Sequence of steps to run.
  steps:
    # Specify the operator to run in each step.
    - operator: read.read_cubes
      # Specify the name of the argument, and its value.
      file_paths: "/data/*.nc"

    - operator: filters.filter_cubes
      # Can specify extra keyword arguments as sub-maps.
      constraint:
        operator: constraints.combine_constraints
        var_constraint:
          # Can nest in another operator to use its output as an argument,
          # multiple levels deep if needed.
          operator: constraints.generate_var_constraint
          # Input implicitly taken from the previous step, but can be overridden
          # by using the appropriate keyword argument.
          varname: m01s03i236
        cell_method_constraint:
          operator: constraints.generate_cell_methods_constraint
          # Values can be more than just strings, such as this empty list.
          cell_methods: []

    # Save a sequence of plots, one per time.
    - operator: plot.spatial_pcolormesh_plot

    # Save a single cube with all the processed data.
    - operator: write.write_cube_to_nc
      overwrite: True

The ``title`` and ``description`` keys provide a human readable description of
what the recipe does. The ``category`` is used to group the produced diagnostics
in the output website.

The ``steps`` key lists the processing steps. The steps are run from top to
bottom, with each step specifying an operator to run, and optionally any
additional inputs to that operator. Each separate step is denoted by a ``-``
under the ``steps:`` key. The operators are specified on the operator key. Its
value should be a string of the form ``module.function``. For additional inputs
the key should be the name of the argument to that operator.

The below code block shows how you can nest operators multiple levels deep. For
details of the specific operators involved, and the arguments that they can
take, see the :doc:`/reference/operators` page.

.. code-block:: yaml

  - operator: filters.filter_cubes
    constraint:
      operator: constraints.combine_constraints
      constraint:
        operator: constraints.generate_stash_constraint
        stash: m01s03i236
      cell_methods_constraint:
        operator: constraints.generate_cell_methods_constraint
        cell_methods: []

.. _YAML 1.2: https://yaml.org/

Using Recipe Variables
----------------------

A CSET recipe may contain variables. These are values filled in at runtime. They
allow making generic recipes that can handle multiple cases. This prevents the
need to have hundreds of recipes for very similar tasks where only minor changes
are required such as switching from mean to median or iterating over a number of
variable names.

A variable can be added to a recipe by setting a parameter's value to the
variable name, prefixed with a dollar sign. This name may only contain upper
case letters and underscores. For example:

.. code-block:: yaml

    key: $MY_VARIABLE

When the recipe is run with ``cset bake`` the variable is replaced with a value
given on the command line. This is done using the variable name as an option,
for example:

.. code-block:: bash

    cset bake -i input -o output -r recipe.yaml --MY_VARIABLE='value'

Alternatively a space can be used between the variable and value:

.. code-block:: bash

    cset bake -i input -o output -r recipe.yaml --MY_VARIABLE value

The given value will be templated into the variable so what runs is actually:

.. code-block:: yaml

    key: value

This can also be used to template into existing values, such as the title.

.. code-block:: yaml

    title: $VARNAME spatial plot
    # When VARNAME is "air_temperature" becomes:
    title: air_temperature spatial plot
