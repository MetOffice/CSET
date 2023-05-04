Usage Guide
===========

.. attention::

    🚧 Section under construction. 🚧

.. toctree::
    :maxdepth: 2

    operator-recipes

Installation
------------

CSET is packaged on `conda-forge`_, so the easiest way to use it is via a simple
``conda install cset``.

If you want to run a development version that has yet to be released the easiest
way is via an editable install. First make sure you have installed and activated
the conda environment.

.. code-block::

    conda create -n cset-dev --file requirements/locks/py310-lock-linux-64.txt
    conda activate cset-dev

Then, from the root of the repository, CSET can be installed with :code:`pip
install -e .`

.. _conda-forge: https://anaconda.org/conda-forge/cset

Usage
-----

cset operators
~~~~~~~~~~~~~~

The chain of operators can be run with ``cset operators path/to/input.pp
path/to/output.nc /path/to/recipe``. Additional help is available with the
``--help`` option. The recipe format is described on the :doc:`operator-recipes`
page.

cset task
~~~~~~~~~

.. attention::

    🚧 Currently unimplemented. 🚧

``cset task [something...]``
