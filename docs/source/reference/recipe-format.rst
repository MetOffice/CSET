Recipe Format
=============

The recipes are text files written in `YAML 1.2`_, a configuration language that
is widely used. They are saved with the ``.yaml`` extension. Below is a
commented example recipe:

.. code-block:: yaml

    category: Category of recipe
    title: Name of recipe
    description: |
      Extended description that can
      go across multiple lines.

    parallel:
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
        filename: intermediate/processed_data
        # intermediate is a slightly special folder for partially processed data
        # that needs collating.

    # Steps to collate processed data into output.
    collate:
      - operator: read.read_cube
        filename: intermediate/*.nc

      # Save a sequence of plots, one per time.
      - operator: plot.plot_spatial_plot

      # Save a single cube with all the processed data.
      - operator: write.write_cube_to_nc

The ``title`` and ``description`` keys provide a human readable description of
what the recipe does. The ``title`` is also used to derive the ID of the running
recipe, used when running the recipe in a workflow. The ``category`` is used to
group the produced diagnostics in the output website.

The ``parallel`` and ``collate`` keys specify lists of processing steps. The
steps are run from top to bottom, with each step specifying an operator to run,
and optionally any additional inputs to that operator. A parallel step is
denoted by a ``-`` under the ``parallel:`` key. The operators are specified on
the operator key. Its value should be a string of the form ``module.function``.
For additional inputs the key should be the name of the argument.

The ``collate:`` key is used for collating together the output of the
parallel steps to produce the final output. This allows for the expensive
processing to be parallelised over many compute nodes, with just the final
visualisation of the data done in a single job to ensure it has all of the data.

The below code block shows how you can nest operators multiple levels deep. For
details of the specific operators involved, and the arguments that can take, see
the :doc:`/reference/operators` page.

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

    parameter: $MY_VARIABLE

When the recipe is run with ``cset bake`` the variable is replaced with a value
given on the command line. This is done using the variable name as an option,
for example:

.. code-block:: bash

    cset bake -i input -o output -r recipe.yaml --MY_VARIABLE='value'

The given value will be templated into the parameter so what runs is actually:

.. code-block:: yaml

    parameter: value
