Getting Started
===============

.. note::

    This section details installing a released version of CSET. Developers
    looking to contribute to CSET should see the :doc:`/contributing/index`
    section instead.

This section contains tutorials suitable for getting started with CSET. By
following them you should learn the basics of using CSET. There are two ways to
run CSET:
1) as a :doc:`command line program <installation>`
2) using a :doc:`cylc workflow <workflow-installation>`.

The command line program uses the CSET python package directly to analyse data
by using pre-existing or custom recipes. The command line program is useful for
ad-hoc or small scale usage, as well as development.

The cylc workflow allows large scale processing of multiple models,
case-studies, and variables. It is however more complex to set up, requiring a
cylc installation. Using the cylc workflow will be what is most widely used by
weather and climate users familiar with rose and cylc_, and requires the least familiarity
with CSET to analyse UM or LFRic output, since the recipes to analyse model runs are already
set up and easily selected.

.. toctree::
    :maxdepth: 1

    installation
    run-recipe
    visualise-recipe
    create-first-recipe
    workflow-installation
    workflow-configure
    workflow-run
    run_full_cylc_workflow

.. _cylc: https://cylc.github.io/
