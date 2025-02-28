Install the command line
========================

.. Tutorial saying how to install CSET. For edge cases should link elsewhere.

For a user of the CSET command line the recommended way to install CSET is via
conda_. It is packaged on `conda-forge`_ in the ``cset`` package. The following
command will install CSET into its own conda environment, which is recommended
to avoid possible package conflicts.

.. caution::

    The example shell snippets in this documentation use ``bash``, and may not
    work with other shells. In particular there are known issues activating
    conda environments with ``ksh``.

.. code-block:: bash

    conda create --name=cset --channel=conda-forge cset

To use CSET, you need to activate the conda environment with the ``conda
activate`` command.

.. code-block:: bash

    conda activate cset

.. note::

    You will have to rerun the ``conda activate cset`` command whenever you use
    a new terminal.

Once that is done, CSET should be ready to use. This can be verified by running
a simple command.

.. code-block:: bash

    cset --version

This command should output the installed version of CSET. This will look
something like ``CSET vX.Y.Z``.

You now have CSET installed. Go to :doc:`the next tutorial to run it
<run-recipe>`.


.. _conda: https://docs.conda.io/en/latest/
.. _conda-forge: https://anaconda.org/conda-forge/cset
