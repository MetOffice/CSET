Usage Guide
===========

.. attention::

    🚧 Section under construction. 🚧

Installation
------------

Currently CSET is not packaged. The way to use it is thus via an editable
install.

First make sure you have installed and activated the conda environment.

.. attention::

    Currently we are awaiting a `pull request
    <https://github.com/MetOffice/CSET/pull/23>`_ being merged to have the
    correct conda environment file. For now use the following command to
    manually install the requirements:

    .. code-block:: bash

        conda install pip setuptools iris mo_pack numpy

From the root of the repository, CSET can be installed with :code:`pip install
-e .`

Usage
-----

The chain of operators can be run with :code:`python3 -m
CSET.run-operators path/to/input.pp path/to/output.nc`
