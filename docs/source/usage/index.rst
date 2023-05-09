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
the easiest way is via an editable install. First make sure you have cloned the
repository onto your computer, then install the conda environment.

.. code-block::

    # If using SSH authentication
    git clone git@github.com:MetOffice/CSET-workflow.git
    # If not
    # git clone https://github.com/MetOffice/CSET-workflow.git
    cd CSET-workflow
    conda create -n cset-dev --file requirements/locks/py310-lock-linux-64.txt
    conda activate cset-dev

Then, from the root of the repository, CSET can be installed with ``pip install
-e .``

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
