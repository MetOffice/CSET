Install the workflow
====================

CSET is often run through a `cylc workflow`_.

The CSET workflow uses **cylc 8**, so you must ensure that is the version of
cylc configured for usage. For the Met Office installation this involves setting
an environment variable before running cylc with the following commands:

.. code-block:: bash

    export CYLC_VERSION=8
    cylc --version  # Check version starts in 8

The first thing you will need to do is to :doc:`install the CSET command line
<installation>`. Once installed, activate the conda environment and run the
``cset extract-workflow`` command to unpack the workflow from inside the CSET
package.

.. code-block:: bash

    # Pick a sensible place to unpack the workflow, such as ~/cylc-src
    cd ~/cylc-src
    # Extract the workflow from CSET into the current working directory.
    cset extract-workflow .
    # Change into the workflow directory.
    cd cset-workflow-vX.Y.Z

Your folder should look like this:

.. code-block:: bash

    $ ls
    app  conda-environment  includes                     lib   opt        rose-suite.conf.example
    bin  flow.cylc          install_restricted_files.sh  meta  README.md  site

If you are at a site with specific CSET integration, you will want to install
the site specific configuration files. This is done by running the
``install_restricted_files.sh`` script. If you are running on your own computer
you can skip this step and later choose ``localhost`` as your site.

.. code-block:: bash

    ./install_restricted_files.sh

You have now installed the CSET workflow. Go to :doc:`the next tutorial to run
it <workflow-run>`.

.. _cylc workflow: https://cylc.github.io/
.. _Releases page on GitHub: https://github.com/MetOffice/CSET/releases
