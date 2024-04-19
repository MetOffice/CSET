Common errors
=============

This page lists common errors, and their solutions.

Workflow run using cylc 7
-------------------------

.. code-block:: text

    [FAIL] 'suite.rc'

CSET is a cylc 8 workflow. You must `install cylc 8`_. Users at the Met Office can
set the ``CYLC_VERSION`` environment variable to ``8`` to enable cylc 8 in their
current terminal. E.g:

.. code-block:: bash

   export CYLC_VERSION=8
   cylc --version  # Check version starts in 8

If you tried to run the workflow with cylc 7, see the next section.

.. _install cylc 8: https://cylc.github.io/cylc-doc/stable/html/installation

Workflow installed using cylc 7
-------------------------------

.. code-block:: text

    WorkflowFilesError: Nested run directories not allowed

If the workflow was first installed with cylc 7, such as via ``rose suite-run``,
the file layout will not be recognised by cylc 8. This can be resolved by
deleting the workflow installation under ``~/cylc-run/cset-workflow``.

WARNING No cubes loaded, check your constraints!
------------------------------------------------

If the workflow complains that no cubes could be loaded this normally requires
you to check your constraints. One constraint that is easily overlooked is the
time constraint. Check that the data you are processing align with your chosen
cycle start point (``CSET_INITIAL_CYCLE_POINT``). You can change this in the
rose GUI under the section "Data and cycling".

The cycling does not work if we are looping over several fields using a single
recipe, but the different fields have different starting times. In this case we
would be trying to plot outside of the time range for some fields causing an
error message that cubes could not be loaded. At the moment the only solution is
to run these variables in different recipes, grouping similar cycling times
together in the same recipe.

Another similar issue occurs when the data processed in the same CSET workflow
have different time intervals. For example ``field1`` has hourly data, whereas
``field2`` has 3 hourly data. We either need to set the ``CSET_CYCLE_PERIOD`` to
``PT3H`` or, if we intend to process the hourly data with a
``CSET_CYCLE_PERIOD`` of 1 hour we need to run two different CSET workflows
instead.
