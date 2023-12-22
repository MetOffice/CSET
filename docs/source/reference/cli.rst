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

    usage: cset bake [-h] -r RECIPE -i INPUT_DIR -o OUTPUT_DIR

    options:
    -h, --help            show this help message and exit
    -r RECIPE, --recipe RECIPE
                            recipe file to read
    -i INPUT_DIR, --input-dir INPUT_DIR
                            directory containing input data
    -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            directory to write output

.. _cset-cookbook-command:

cset cookbook
~~~~~~~~~~~~~

Saves the included recipe files to a local directory. This allows access to
pre-created recipes for many common tasks. See :doc:`/usage/operator-recipes`
for descriptions of available recipes.

.. code-block:: text

    usage: cset cookbook [-h] [-o OUTPUT_DIR] [-l] [recipe]

    positional arguments:
    recipe                recipe to output or detail. Omit for all.

    options:
    -h, --help            show this help message and exit
    -o OUTPUT_DIR, --output-dir OUTPUT_DIR
                            directory to save recipes. If omitted uses $PWD
    -l, --list            list available recipes. Supplied recipes are detailed.

.. _cset-graph-command:

cset graph
~~~~~~~~~~

Visualise a recipe. This renders a graph representing the recipe, and saves it
to a temporary file, which is automatically opened. If the ``--details`` option
is specified it also includes operator arguments in the output, so you can see
exactly what ran.

.. code-block:: text

    usage: cset graph [-h] -r RECIPE [-o [OUTPUT_PATH]] [-d]

    options:
    -h, --help            show this help message and exit
    -r RECIPE, --recipe RECIPE
                            recipe file to read
    -o [OUTPUT_PATH], --output-path [OUTPUT_PATH]
                            file in which to save the graph image, otherwise uses a temporary file. When specified the file is not automatically opened
    -d, --details         include operator arguments in output

.. image:: recipe-graph.svg
    :alt: A graph visualising a recipe. The nodes are linked with directed edges showing the flow of data.
