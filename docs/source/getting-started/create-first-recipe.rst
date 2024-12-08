Creating your first custom recipe
=================================

.. Tutorial guiding through how to create a simple custom recipe.
.. Should include an overview of the recipe format.

In this tutorial we will write a new recipe from scratch.

CSET recipes are written in `YAML 1.2`_, a data format used by many pieces of
software. Even if you've never seen it before don't worry, as this tutorial
should cover everything you need to know.

Recipes consist mostly of key-value pairs, which in YAML are denoted with the
key on the left of a colon, and the value on the right. The value can be a
string, a number, or even more key-value pairs by indenting them below the key.
It is important to note that, like in python, indentation is significant in
YAML. Indentation should be done with two spaces.

.. code-block:: yaml

  # Simple YAML example.
  key: value
  key2:
    key-as-value: value

.. _YAML 1.2: https://en.wikipedia.org/wiki/YAML

Making a new recipe
-------------------

We will now create a recipe from scratch. This recipe will plot a specific
timestamp of the example air temperature data.

Start by opening a new file in your favourite text editor, and save it somewhere
accessible as ``surface_air_temperature_spatial_plot.yaml``.

Recipe Metadata
---------------

Title
~~~~~

The first thing we will add to our recipe file is some metadata about the recipe
itself, starting with its title.

The title is the name of the recipe. It should be sufficiently descriptive so
you can tell what the recipe does without any further context. It shows up in
the output page, the plot title, and a few other places.

.. code-block:: yaml

    title: Mean Surface Air Temperature Spatial Plot

Description
~~~~~~~~~~~

Following the title we have the description. This is a long-form description of
what the recipe does, considerations around its use, and what science it is
based on. The description is `Markdown`_, so some formatting can be used where
helpful, papers can be linked, and so on. A little bit of unusual syntax here is
``description: |``, with the pipe after the key. This means the indented block
that follows is a multiline string, so you can have as many lines as you want,
provided they are all indented with at least two spaces.

.. _Markdown: https://commonmark.org/help/

.. code-block:: yaml

    description: |
      Extracts and plots the 1.5m air temperature from a file. The temperature
      is averaged across the time coordinate.


Recipe Steps
------------

When baking you follow a recipe step-by-step, CSET does the same with its
recipes. The steps of the recipe are contained within the ``steps`` key. Each
block prefixed with a ``-`` (which makes a list in YAML) is an individual step,
and they are run in order from top to bottom.

Each step has an ``operator`` key, which specifies which operator to use. A
`complete list of operators is in the documentation`_, but for this tutorial we
will describe them here.

.. _complete list of operators is in the documentation: https://metoffice.github.io/CSET/reference/operators

The first step reads in the model data. This is done with the
``read.read_cubes`` operator. The first step is special, and receives the path
to the input data as its implicit input.

.. code-block:: yaml

    steps:
      - operator: read.read_cubes

Once we have read the data, we need to filter them down to the data we require
for our computations. ``filter.filter_cubes`` is the operator for that. It also
ensures that the CubeList returned by ``read.read_cubes`` is turned into a Cube.

.. code-block:: yaml

    # Filter operator
      - operator: filters.filter_cubes
        constraint:
          operator: constraints.combine_constraints
          stash_constraint:
            operator: constraints.generate_stash_constraint
            stash: m01s03i236
          cell_methods_constraint:
            operator: constraints.generate_cell_methods_constraint
            cell_methods: []

Unlike the ``read.read_cubes`` operator, we have many key-value pairs in this
step. The other keys in the step are the named arguments that operator takes.
Each operator implicitly takes its first argument from the previous step, but
this can be overridden by explicitly providing it.

Note that arguments of operators can themselves be operators. This allows
nesting operators to use their output as arguments to other operators.

Next we reduce the dimensionality of the data ahead of plotting. In this case we
chose the mean of the time coordinate. The ``collapse.collapse`` operator allows
us to do this, and takes as parameters the coordinate to collapse, and the
method by which it is done.

.. code-block:: yaml

    # Collapse operator
      - operator: collapse.collapse
        coordinate: time
        method: MEAN

Finally we plot the model data, using the ``plot.spatial_contour_plot``
operator, and then save the processed data with the ``write.write_cube_to_nc``
operator. This finishes up our recipe.

.. code-block:: yaml

    # Plotting and writing operators
      - operator: plot.spatial_contour_plot

      - operator: write.write_cube_to_nc


Complete Recipe
---------------

After following this far your recipe should look like this:

.. code-block:: yaml

    title: Mean Surface Air Temperature Spatial Plot
    description: |
      Extracts and plots the 1.5m air temperature from a file. The temperature
      is averaged across the time coordinate.

    steps:
      - operator: read.read_cubes

      - operator: filters.filter_cubes
        constraint:
          operator: constraints.combine_constraints
          stash_constraint:
            operator: constraints.generate_stash_constraint
            stash: m01s03i236
          cell_methods_constraint:
            operator: constraints.generate_cell_methods_constraint
            cell_methods: []

      - operator: collapse.collapse
        coordinate: time
        method: MEAN

      - operator: plot.spatial_contour_plot

      - operator: write.write_cube_to_nc

Running the Recipe
------------------

We can run this recipe using the same data as was used for the
:doc:`run-recipe` tutorial: :download:`air_temp.nc`

Use ``cset bake`` to run your newly created recipe.

.. code-block:: bash

    cset bake -i air_temp.nc -o output/ -r surface_air_temperature_spatial_plot.yaml

You can investigate the created plot and data file in the specified ``output``
directory.

You've now successfully written and run a custom CSET recipe.
