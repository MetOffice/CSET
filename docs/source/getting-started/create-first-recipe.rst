Creating your first custom recipe
=================================

.. Tutorial guiding through how to create a simple custom recipe.
.. Should include an overview of the recipe format.

.. code-block:: yaml
    :emphasize-lines: 1

    title: Mean Surface Air Temperature Spatial Plot
    description: |
      Extracts and plots the 1.5m air temperature from a file. The temperature
      is averaged across the time coordinate.

    steps:
      - operator: read.read_cubes
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
        file_path: CSET_OUTPUT_PATH

      - operator: write.write_cube_to_nc
        file_path: CSET_OUTPUT_PATH

The title of the recipe is highlighted.

.. TODO: Write what should go here.

.. code-block:: yaml
    :emphasize-lines: 2-4

    title: Mean Surface Air Temperature Spatial Plot
    description: |
      Extracts and plots the 1.5m air temperature from a file. The temperature
      is averaged across the time coordinate.

    steps:
      - operator: read.read_cubes
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
        file_path: CSET_OUTPUT_PATH

      - operator: write.write_cube_to_nc
        file_path: CSET_OUTPUT_PATH

The description is highlighted.

.. TODO: Write what should go here.

.. code-block:: yaml
    :emphasize-lines: 7-15

    title: Mean Surface Air Temperature Spatial Plot
    description: |
      Extracts and plots the 1.5m air temperature from a file. The temperature
      is averaged across the time coordinate.

    steps:
      - operator: read.read_cubes
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
        file_path: CSET_OUTPUT_PATH

      - operator: write.write_cube_to_nc
        file_path: CSET_OUTPUT_PATH

The first operator is highlighted.

.. TODO: Write what should go here.
