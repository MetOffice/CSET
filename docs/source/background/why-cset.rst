Why use CSET?
=============

When evaluating weather and climate models we are trying to understand the
characteristics of our model configurations, the physical processes that lead to
biases, and how they compares to other models (physical and machine learned),
model configurations and observations. This is an iterative process, and each
step of evaluation unveils more questions that need investigations. Evaluation
often follows an individual approach by researchers spending significant
resource on scientific and technical development.

CSET aids in this by providing a flexible way to interrogate model data, using
diagnostics that can be quickly created by the combination of operators in
:doc:`/usage/operator-recipes`. Common operations such as reading, writing, and
regridding are provided to reduce duplication of effort.

CSET provides a legacy for user-developed evaluation methods and diagnostics to
be shared and documented, with :doc:`well-defined working practices and review
processes</contributing/index>` to ensure best practice for evaluation and
verification linked to convective- and turbulence-scale model configurations.
Therefore, it provides many benefits in reproducibility, portability,
accessibility, maintainability, and quality assurance. By contributing newly
developed diagnostics to CSET you ensure their legacy, ensure their quality
assurance and benefit to the entire modelling community. Furthermore, any
operators that the community finds especially useful will be contributed back to
METplus_, so they can serve an even wider community.

.. _METplus: https://dtcenter.org/community-code/metplus
