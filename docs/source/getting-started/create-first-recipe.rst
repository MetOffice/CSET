Creating your first custom recipe
=================================

.. Tutorial guiding through how to create a simple custom recipe.
.. Should include an overview of the recipe format.

In this tutorial we will look at the recipe format CSET uses, and create a new
recipe from scratch.

CSET recipes are written in YAML 1.2, a data format used by many pieces of
software. Even if you've never seen it before don't worry, as this tutorial
should cover everything you need to know.

Recipes consist mostly of key-value pairs, which in YAML are denoted with the
key on the left of a colon, and the value on the right. The value can be a
string, a number, or even more key-value pairs by indenting them below the key.
It is important to note that, like in python, indentation is significant in
YAML. Indentation should be done with two spaces.

Recipe Metadata
---------------

The first thing in a recipe file is some metadata about the recipe itself.

.. code-block:: yaml
    :emphasize-lines: 1-4

    title: Mean Surface Air Temperature Spatial Plot
    description: |
      Extracts and plots the 1.5m air temperature from a file. The temperature
      is averaged across the time coordinate.

    steps:
      - operator: read.read_cubes
        constraint:
          operator: constraints.generate_stash_constraint
          stash: m01s03i236

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
        filename: CSET_OUTPUT_PATH

      - operator: write.write_cube_to_nc
        filename: CSET_OUTPUT_PATH

The title is the name of the recipe. It should be sufficiently descriptive so
you can tell what the recipe does without any further context. It shows up in
the output page, the plot title, and a few other places.

Next we have the description. This is a long-form description of what the recipe
does, considerations around its use, and what science it is based on. The
description is `markdown`_, so some formatting can be used were helpful, papers
can be linked, and so on. A little bit of unusual syntax here is ``description:
|``, with the pipe after the key. This means the indented block that follows is
a multiline string, so you can have as many lines as you want, provided they are
all indented with at least two spaces.


Recipe Steps
------------

Just as in baking you would follow a recipe step-by-step, so does CSET.

.. code-block:: yaml
    :emphasize-lines: 6-

    title: Mean Surface Air Temperature Spatial Plot
    description: |
      Extracts and plots the 1.5m air temperature from a file. The temperature
      is averaged across the time coordinate.

    steps:
      - operator: read.read_cubes
        constraint:
          operator: constraints.generate_stash_constraint
          stash: m01s03i236

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
        filename: CSET_OUTPUT_PATH

      - operator: write.write_cube_to_nc
        filename: CSET_OUTPUT_PATH

The steps of the recipe are all under the ``steps`` key. Each block prefixed
with a ``-`` is a step, and they are run in order.

Each step has an ``operator`` key, which specifies which operator to use. A
`complete list of operators is in the documentation`_. The other keys in a step
are the arguments that operator takes. Each operator implicitly takes its first
argument from previous step, but this can be overridden by explicitly providing
it. The first step receives the path to the input data as its implicit input.

The other thing to note is that the arguments of operators can themselves be
operators. This allows nesting operators to use their output as arguments to
other operators.

.. _complete list of operators is in the documentation: https://metoffice.github.io/CSET/reference/operators

Making a new recipe
-------------------

.. TODO: Write section.

.. Do a contour plot of a single timestamp.
