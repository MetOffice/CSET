Getting Started
===============

This section contains tutorials suitable for getting started with CSET. By
following them you should learn the basics of using CSET.

.. note::

    This section details installing a released version of CSET. Developers
    looking to contribute to CSET should see the :doc:`/contributing/index`
    section instead.

There are two ways to run CSET: as a :doc:`command line program <installation>`,
or using a :doc:`cylc workflow <run_full_cylc_workflow>`.

The command line program uses the CSET python package directly to analyse data
by using pre-existing or custom recipes. The command line program can be used to
run a single recipe at a time, useful for ad-hoc or small scale usage, and
development. :doc:`Follow this tutorial for how to use the command line program
<installation>`.

The cylc workflow allows large scale processing of multiple models,
case-studies, and variables. It is, however, more complex to set up and requires a
cylc installation. Using the cylc workflow will be what is most widely used by
weather and climate users familiar with rose and cylc_, and requires the least
familiarity with CSET to analyse UM or LFRic output, since the recipes to
analyse model runs are already set up and easily selected. :doc:`Follow this
tutorial for how to use the workflow <run_full_cylc_workflow>`.

.. toctree::
    :maxdepth: 1

    installation
    run-recipe
    visualise-recipe
    create-first-recipe
    run_full_cylc_workflow

.. _cylc: https://cylc.github.io/
