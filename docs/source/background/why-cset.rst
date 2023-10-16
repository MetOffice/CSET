Why use CSET?
=============

When evaluating weather models you are trying to understand the processes that
lead to biases in our model configurations, and how that compares to other
models and observations. This can be a very iterative process, and each step of
evaluation unveils more questions that need investigations.

CSET aids in this by providing a flexible way to interrogate model data, using
diagnostics that can be quickly created by the combination of operators in
:doc:`/usage/operator-recipes`. Common operations such as reading, writing, and
regridding are provided to reduce duplication of effort.

CSET is a centralised place for custom diagnostics to live, with well defined
:doc:`/contributing/index` to ensure that they stay maintained. By contributing
diagnostics to CSET you ensure that they outlive the paper they were written
for, and benefit the entire modelling community. Furthermore, any operators that
the community finds especially useful will be contributed back to METplus_, so
they can serve an even wider community.

It aims to align parametrisation, diagnostic development and evaluation research
linked to Met Office Research Atmosphere Land suites (RAL) across the Met Office
and UM partnership. Apart from verification capabilities it focusses on
providing and continuously developing a centralised source of tools to aid
process-oriented evaluation for UM and LFRic systems supporting deterministic
models and ensembles. It supports community development of well documented and
peer reviewed evaluation tools and provides a legacy for diagnostics and
observations. It offers flexible evaluation code that users can easily adapt
according to their needs. It is build on a modern software stack using Python3
and Met+ in a conda environment to support portability. Clear documentation,
working practices, automatic testing, and open access ensure developers can
easily use and contribute to this system.

.. _METplus: https://dtcenter.org/community-code/metplus
