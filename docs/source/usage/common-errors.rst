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

If the workflow complains that no cubes could be loaded this normally requires you to
check your constraints. One constraint that is easily overlooked is the time constraint.
Check that the data you are processing align with your start cycle point 
(CSET_INITIAL_CYCLE_POINT). You can change this in the rose gui under the section 
"Data and cycling". One problem we have encountered is when we are looping over several 
fields using a single recipe, but the different fields have different starting times.
At the moment the only solution is to run these variables in different recipes i.e. group 
similar cyclign times in the same recipe together.
