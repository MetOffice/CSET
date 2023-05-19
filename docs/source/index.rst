CSET Documentation
==================

.. toctree::
   :hidden:

   usage/index
   working-practices/index
   operators
   genindex
   GitHub <https://github.com/MetOffice/CSET>

.. note::

   This is where we should write a high level introduction to CSET and have
   some useful links to other related resources.

CSET is a tool to aid in evaluating regional model configurations. It aims to
replace the collection of bespoke scripts littering people's home directories,
reducing effort wasted on duplicating already existing code. This centralisation
of diagnostics should also make evaluations more consistent and comparable.
Development takes place in the `CSET repository on GitHub`_.

Use the side bar to the left to access other pages of the documentation.

Why use CSET?
-------------

When evaluating weather models you are trying to figure out what processes are
happening inside the model, and how that compares to other models and reality.
This is a very iterative process, and each step of evaluation unveils more
questions that need investigations.

CSET aids in this by providing a quick way to interrogate model data, using
diagnostics that can be quickly created by the combination of :doc:`operators`
in an :doc:`usage/operator-recipe`.

CSET also is a centralised place for custom diagnostics to live, with well
defined :doc:`working-practices/index` to ensure that they stay maintained. By
constributing diagnostics to CSET you ensure that they outlive the paper they
were written for, and benifit the entire modelling community.

.. _CSET repository on GitHub: https://github.com/MetOffice/CSET

Licence
-------

Copyright © 2022-2023 Met Office and contributors. CSET is distributed under the
`Apache 2.0 License`_, in the hope that it will be useful.

.. _Apache 2.0 License: https://www.apache.org/licenses/LICENSE-2.0
