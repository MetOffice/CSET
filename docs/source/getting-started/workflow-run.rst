Run the workflow
================

After configuration via the rose GUI, the CSET workflow is ready to run.

To run the workflow, use ``cylc vip``. You can view the job's progress with the
cylc GUI, accessible with the command ``cylc gui``.

.. code-block:: bash

    # Run workflow from the current working directory.
    cylc vip .
    # Monitor the workflow's progress.
    cylc gui


Other commands to control the workflow are described in the cylc_ documentation.


Once CSET has finished running you will receive an email containing a link to
the output page.

.. _cylc: https://cylc.github.io/cylc-doc/stable/html/user-guide/running-workflows/index.html
