CSET Documentation
==================

.. toctree::
   :hidden:

   usage/index
   working-practices/index
   operators
   genindex
   GitHub <https://github.com/MetOffice/CSET>

:abbr:`CSET (Convective Scale Evaluation Tool)` is a tool to aid in verifying
and evaluating convective-scale and turbulence-scale (regional and increasingly
global) model configurations. It aims to replace the RMED RES and Toolbox and
the collections of bespoke scripts littering people's home directories, reducing
effort wasted on duplicating already existing code. This centralisation of
diagnostics should also make evaluations more consistent, reproducible and
comparable. Development takes place in the `CSET repository on GitHub`_.

Use the side bar to the left to access other pages of the documentation.

Why use CSET?
-------------

When evaluating weather models you are trying to understand the processes that
lead to biases in our model configurations, and how that compares to other
models and observations. This can be a very iterative process, and each step of
evaluation unveils more questions that need investigations.

CSET aids in this by providing a flexible way to interrogate model data, using
diagnostics that can be quickly created by the combination of :doc:`operators`
in an :doc:`usage/operator-recipes`. Common operations such as reading, writing,
and regridding are provided to reduce duplication of effort.

CSET is a centralised place for custom diagnostics to live, with well defined
:doc:`working-practices/index` to ensure that they stay maintained. By
contributing diagnostics to CSET you ensure that they outlive the paper they
were written for, and benefit the entire modelling community. Furthermore, any
operators that the community finds especially useful will be contributed back to
[METplus](https://dtcenter.org/community-code/metplus), so they can serve an
even wider community.

.. _CSET repository on GitHub: https://github.com/MetOffice/CSET

Licence
-------

Copyright © 2022-2023 Met Office and contributors. CSET is distributed under the
`Apache 2.0 License`_, in the hope that it will be useful.

.. _Apache 2.0 License: https://www.apache.org/licenses/LICENSE-2.0
