Install the workflow
====================

CSET is typically run through a `cylc workflow`_.

CSET uses **cylc 8**, so you must ensure that is the version of cylc configured
for usage. For the Met Office installation this involves setting an environment
variable before running cylc with the following commands:

.. code-block:: bash

    export CYLC_VERSION=8
    cylc --version  # Check version starts in 8

The first thing you will need to do is download the CSET workflow from the
`Releases page on GitHub`_. Download the ``cset-workflow-vX.Y.Z.tar.gz`` tarball,
which contains everything you need to run the workflow. Once downloaded the
tarball can be unpacked to a location of your choosing.

.. code-block:: bash

    # Pick a sensible place to unpack the archive, such as ~/cylc-src
    cd ~/cylc-src
    # Change to the appropriate version number for the release you are using.
    tar -xf ~/Downloads/cset-workflow-vX.Y.Z.tar.gz

Once unpacked enter the ``cset-workflow`` directory; All the following commands
assume you are within it.

.. code-block:: bash

    # Change into the workflow directory.
    cd cset-workflow-vX.Y.Z

If you are at a site with specific CSET integration, you need to install the
site specific configuration files. This is done by running the
``install_restricted_files.sh`` script. If you are running on your own computer
you can skip this step and later choose ``localhost`` as your site.

.. code-block:: bash

    ./install_restricted_files.sh

Your folder should look like this:

.. code-block:: bash

    $ ls
    app  flow.cylc  install_restricted_files.sh  meta       requirements             site
    bin  includes   lib                          README.md  rose-suite.conf.example

You have now installed the CSET workflow. Go to :doc:`the next tutorial to run
it <workflow-run>`.

.. _cylc workflow: https://cylc.github.io/
.. _Releases page on GitHub: https://github.com/MetOffice/CSET/releases
