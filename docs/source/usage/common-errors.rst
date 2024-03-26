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
