Usage Guide
===========

.. attention::

    🚧 Section under construction. 🚧

.. toctree::
    :maxdepth: 2

    operator-recipes

Installation
------------

The recommended way to install CSET is via conda. It is packaged on
`conda-forge`_ and can be installed with a simple ``conda install -c conda-forge
cset``.

If you instead want to run a development version that has yet to be released,
the easiest way is via an editable install. You can learn how to do this in the
:ref:`working_practices_getting_started` section of the
:doc:`../working-practices/index`.

.. _conda-forge: https://anaconda.org/conda-forge/cset

Usage
-----

cset operators
~~~~~~~~~~~~~~

The chain of operators can be run with ``cset operators /path/to/recipe
path/to/input.pp path/to/output.nc``. Additional help is available with the
``--help`` option. The recipe format is described on the :doc:`operator-recipes`
page.

.. code-block:: text

    usage: cset operators [-h] recipe_file input_file output_file

    positional arguments:
    recipe_file  recipe file to execute
    input_file   input file to read
    output_file  output file to write

    options:
    -h, --help     show this help message and exit
    -v, --verbose  increase output verbosity, may be specified multiple times
