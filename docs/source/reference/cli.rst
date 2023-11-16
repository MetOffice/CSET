CLI Usage
=========

.. _cset-bake-command:

cset bake
~~~~~~~~~

Used to run a recipe on some data. The recipe, input file, and a path to an
output file must be provided. Additional help is available with the ``--help``
option. The recipe format is described on the :doc:`/usage/operator-recipes` page. If
recipe_file is omitted from the command line, the recipe will be read from the
``CSET_RECIPE`` environment variable instead. This environment variable should
contain the YAML text that you want executed.

.. code-block:: text

    usage: cset bake [-h] input_file output_file [recipe_file]

    positional arguments:
    input_file   input file to read
    output_dir   directory to write output
    recipe_file  recipe file to execute. If omitted reads from CSET_RECIPE environment variable

    options:
    -h, --help   show this help message and exit

.. _cset-cookbook-command:

cset cookbook
~~~~~~~~~~~~~

Saves the included recipe files to a local directory. This allows access to
pre-created recipes for many common tasks. See [LINK TO DOCUMENTATION PAGE ON
RECIPES] for descriptions of available recipes.

.. code-block:: text

    usage: cset cookbook [-h] [recipe_dir]

    positional arguments:
    recipe_dir  directory to save recipes. If omitted uses $PWD/recipes

    options:
    -h, --help  show this help message and exit

.. _cset-graph-command:

cset graph
~~~~~~~~~~

Visualise a recipe. This renders a graph representing the recipe, and saves it
to a temporary file, which is automatically opened. If the ``--detailed`` option
is specified it also includes operator arguments in the output, so you can see
exactly what ran.

.. image:: recipe-graph.svg
    :alt: A graph visualising a recipe. The nodes are linked with directed edges showing the flow of data.

.. code-block:: text

    usage: cset graph [-h] [-o [OUTPUT_PATH]] [-d] [recipe]

    positional arguments:
    recipe                recipe file to read. If omitted reads from CSET_RECIPE environment variable

    options:
    -h, --help            show this help message and exit
    -o [OUTPUT_PATH], --output_path [OUTPUT_PATH]
                            file in which to save the graph image, otherwise uses a temporary file. When specified the file is not automatically opened
    -d, --details         include operator arguments in output
