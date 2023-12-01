Install and run the CSET workflow
=================================

CSET is typically run through a `cylc workflow`_. As long as cylc 8 is setup at
your site (which is beyond the scope of this guide), then this guide takes you
through installing the workflow.

The first thing you will need to do is to download the CSET workflow. The
easiest way to do that is via the `Releases`_ page on GitHub, or you can clone
the repository. Once downloaded the tarball or zip can be unpacked to a location
of your choosing.

CSET uses **cylc 8**, so you must ensure that is the version of cylc configured
for usage. For the Met Office installation this involves setting an environment
variable before running cylc with the following commands:

.. code-block::bash

   export CYLC_VERSION=8
   cylc --version  # Check version starts in 8

You will then need to edit the configuration to set up your job. Start by making
a copy of the ``rose-suite.conf.example`` file called ``rose-suite.conf``. This
needs further amendments, which are done using `rose edit`_, a GUI tool that
makes configuration files more tractable. Within rose edit go through the
sections under "suite conf" and fill in the config. Help text can be viewed by
clicking on the name of a variable. Once you have configured CSET, you can save
and close rose edit.

Opening a command line inside the root of the CSET folder you can run it with
the command ``cylc vip .``, which will cause cylc to submit the job to your
site's batch processing system, and run it. You can view the job's progress with
the cylc gui, accessible with the command ``cylc gui``.

Once CSET has finished running you will receive an email containing a link to
the output page.

.. _cylc workflow: https://cylc.github.io/
.. _Releases: https://github.com/MetOffice/CSET/releases
.. _rose edit: https://metomi.github.io/rose/doc/html/api/command-reference.html#rose-config-edit
