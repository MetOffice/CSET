CLI Usage
=========

.. _cset-bake-command:

cset bake
~~~~~~~~~

Used to run a recipe on some data. The recipe, input directory, and output
directory must be provided. Additional help is available with the ``--help``
option. The recipe format is described on the :doc:`/usage/operator-recipes`
page.

.. code-block:: text

    usage: cset bake [-h] -i INPUT_DIR -o OUTPUT_DIR -r RECIPE

    options:
    -h, --help            show this help message and exit
    -i INPUT_DIR, --input-dir INPUT_DIR
                            directory containing input data
    -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            directory to write output into
    -r RECIPE, --recipe RECIPE
                            recipe file to read

.. _cset-cookbook-command:

cset cookbook
~~~~~~~~~~~~~

Saves an included recipe file to a local directory. This allows access to
pre-created recipes for many common tasks. See :doc:`/usage/operator-recipes`,
or use ``--details`` for descriptions of available recipes.

.. code-block:: text

    usage: cset cookbook [-h] [-d] [-o OUTPUT_DIR] [recipe]

    positional arguments:
    recipe                recipe to output or detail

    options:
    -h, --help            show this help message and exit
    -d, --details         list available recipes. Supplied recipes are detailed.
    -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            directory to save recipes. If omitted uses $PWD

.. _cset-graph-command:

cset graph
~~~~~~~~~~

Visualise a recipe. This renders a graph representing the recipe, and saves it
to a temporary file, which is automatically opened. If the ``--details`` option
is specified it also includes operator arguments in the output, so you can see
exactly what ran.

.. code-block:: text

    usage: cset graph [-h] [-d] [-o [OUTPUT_PATH]] -r RECIPE

    options:
    -h, --help            show this help message and exit
    -d, --details         include operator arguments in output
    -o [OUTPUT_PATH], --output-path [OUTPUT_PATH]
                            persistent file to save the graph. Otherwise the file is opened
    -r RECIPE, --recipe RECIPE
                            recipe file to read

.. image:: recipe-graph.svg
    :alt: A graph visualising a recipe. The nodes are linked with directed edges showing the flow of data.
