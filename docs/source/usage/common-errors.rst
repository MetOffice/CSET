Common errors
=============

This page lists common errors, and their solutions.


Workflow installed using cylc 7
-------------------------------

.. code-block:: text

    WorkflowFilesError: Nested run directories not allowed

If the workflow was first installed with cylc 7, such as via ``rose suite-run``,
the file layout will not be recognised by cylc 8. This can be resolved by
deleting the workflow installation under ``~/cylc-run/cset-workflow``.
