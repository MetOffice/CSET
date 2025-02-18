Set-up code and tooling
=======================

Contributing
------------

Contributions are readily welcome! In addition to reading the `working
practices`_, the key recommendation is early communication. Open an issue on
Github with your proposed change or addition in the design phase, and then
others can provide guidance early. To create an issue:

- Go to the `issue tracker on GitHub`_,
- Search for existing issues that cover what you want changed,
- If none exist the use the green "New Issue" button in the top right corner to
  create a new one.

It is also good to make a :ref:`Pull Request (PR) <pull-request>` early, even
before your code is complete. You can indicate it is still a work in progress
with the `draft pull request functionality of GitHub`_, or putting ``WIP`` in the
PR title.

.. _issue tracker on GitHub: https://github.com/MetOffice/CSET/issues
.. _working practices: https://metoffice.github.io/CSET/contributing/
.. _draft pull request functionality of GitHub: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/about-pull-requests#draft-pull-requests

Before you get to coding, there are a few steps you need to do to setup the
development environment.

.. _getting-the-code:

Getting the code
----------------

Git is a version control software, which makes collaborating on software much
easier. If you are new to git have a look at the :doc:`git` page to get started.

To get the code onto your computer, you need to clone it with git. Most
:abbr:`IDEs (Integrated Development Environments)` include the ability to do
this in their interfaces, but from the command line it can be done with one of
the following commands:

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

.. _setup_tooling:

Setting up tooling
------------------

To be able to run the tests or build the documentation you need some
prerequisite software. The easiest way to get this is with `conda`_. The
following commands, when run from within the CSET directory, will setup a conda
environment for you to use.

.. code-block:: bash

    # Creates a conda environment named "cset-dev".
    conda create -n cset-dev --file requirements/locks/py313-lock-linux-64.txt
    # Activates the conda environment.
    conda activate cset-dev
    # Adds extra checks when you commit something with git.
    pre-commit install
    # Make CSET runnable for manual testing
    pip install -e .

When subsequently returning to the code after closing your terminal, you will
need to rerun the ``conda activate cset-dev`` command.

.. _conda: https://docs.conda.io/en/latest/

Updating tooling
------------------

If it has been some time since you created your conda environment it might be
worth recreating it to get the latest tools and dependencies.

.. code-block:: bash

    # List all your conda environments
    conda info --envs
    # Remove old conda environment.
    conda remove -n cset-dev --all -y

Then follow the steps under :ref:`setup_tooling` again.
