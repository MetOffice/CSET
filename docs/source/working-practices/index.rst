Working Practices
=================

To aid in the development of CSET we are adopting some working practices so
everyone involved knows what to expect. On this page is everything you need to
get started, and the links below go into more detail on specific topics.

.. toctree::
    :maxdepth: 2

    pull-requests
    git
    testing
    documentation
    code-review
    releases
    backwards-compatibility


Getting Started
---------------

Before you can get to coding, there are a few steps you need to do.

Setting up git
~~~~~~~~~~~~~~

git is a version control software, which makes collaborating on software much
easier. If you are new to git you'll need to perform the steps in this
subsection, and I'd recommend keeping a `git cheat sheet`_ handy, and looking at
the :doc:`git` page of this documentation.  The following
command will set yourself up on git, and only have to be done once.

.. code-block:: bash

    git config --global user.name "Your Name"
    git config --global user.email "your-email@example.com"

To get the code onto your computer, you need to clone it with git. Most IDEs
include the ability to do this in their interfaces, but from the command line it
can be done with the following command:

.. code-block:: bash

    git clone https://github.com/MetOffice/CSET.git

This will download a copy of the repository (where the code is stored), and all
of its history onto your computer. From there we need to setup a few things
before we can develop.

.. _git cheat sheet: https://education.github.com/git-cheat-sheet-education.pdf

Setting up tooling
~~~~~~~~~~~~~~~~~~

To be able to run the tests of build the documentation you need some
prerequisite software. The easiest way to get this is with conda. The following
command will setup a conda environment for you to use. When subsequently
returning to the code after closing your terminal, you may need to rerun the
:code:`conda activate cset-dev` command.

.. code-block:: bash

    # Creates a conda environment. This command can be slow.
    conda env create --file environment.yml
    # Activates the conda environment.
    conda activate cset-dev
    # Adds extra checks when you commit something with git.
    pre-commit install

Contributing
------------

Contributions are readily welcome! In addition to reading the working practices
linked above, the key recommendation is early communication. Open an `issue on
Github`_ with your proposed change or addition in the design phase, and then
other can provide guidance early, instead of possibly rejecting work at the
review stage after you have spent weeks working on it.

.. _issue on GitHub: https://github.com/MetOffice/CSET/issues
