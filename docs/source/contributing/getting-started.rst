Getting Started with Contributing
=================================

Before you can get to coding, there are a few steps you need to do.

Getting the code
----------------

Git is a version control software, which makes collaborating on software much
easier. If you are new to git have a look at the :doc:`git` page to get started.

To get the code onto your computer, you need to clone it with git. Most IDEs
include the ability to do this in their interfaces, but from the command line it
can be done with one of the following commands:

.. code-block:: bash

    # Via SSH (Recommended)
    git clone git@github.com:MetOffice/CSET.git

    # Via HTTPS
    git clone https://github.com/MetOffice/CSET.git

This will download a copy of the repository (where the code is stored), and all
of its history onto your computer. From there we need to setup a few things
before we can develop.

.. note::

    If you have previously cloned the repository you can update it with the
    latest changes. Ensure all changes are committed, then run ``git pull``.

Setting up tooling
------------------

To be able to run the tests or build the documentation you need some
prerequisite software. The easiest way to get this is with `conda_`. The
following commands, when run from within the CSET directory, will setup a conda
environment for you to use.

.. code-block:: bash

    # Creates a conda environment named "cset-dev".
    conda create -n cset-dev --file requirements/locks/py311-lock-linux-64.txt
    # Activates the conda environment.
    conda activate cset-dev
    # Adds extra checks when you commit something with git.
    pre-commit install
    # Make CSET runnable for manual testing
    pip install -e .

When subsequently returning to the code after closing your terminal, you may
need to rerun the ``conda activate cset-dev`` command.

.. _conda: https://docs.conda.io/en/latest/

Contributing
------------

Contributions are readily welcome! In addition to reading the working practices
linked above, the key recommendation is early communication. Open an `issue on
Github`_ with your proposed change or addition in the design phase, and then
others can provide guidance early. It is also good to make a pull request early,
even before your code is complete, using either the Draft pull request
functionality of GitHub, or putting ``WIP`` in the title to indicate it is still
a work in progress.

.. _issue on GitHub: https://github.com/MetOffice/CSET/issues
