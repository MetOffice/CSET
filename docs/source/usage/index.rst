Usage Guide
===========

.. attention::

    🚧 Section under construction. 🚧

.. toctree::
    :maxdepth: 2

    operator-recipes

Installation
------------

Currently CSET is not packaged. The way to use it is thus via an editable
install.

First make sure you have installed and activated the conda environment.

.. code-block::

    conda create -n cset-dev --file requirements/locks/py310-lock-linux-64.txt
    conda activate cset-dev

Then, from the root of the repository, CSET can be installed with :code:`pip install
-e .`

Usage
-----

The chain of operators can be run with :code:`python3 -m
CSET.operators /path/to/recipe path/to/input.pp path/to/output.nc`
