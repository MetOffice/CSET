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
the community finds especially useful will be contributed back to
METplus_, so they can serve an
even wider community.

.. _METplus: https://dtcenter.org/community-code/metplus
