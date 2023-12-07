Why use the workflow?
=====================

This workflow has two main use cases: Evaluation, and verification.

It aids in evaluation by providing an easy and reproducible way of running many
diagnostics over a number of datasets, as well as providing additional
functionality over the command line tool for things like comparing models
against each other and observations. It is particularly useful in the initial
stages of an investigation, when you are trying to find an area of interest for
deeper study and need to flexibly change the order of operators or add bespoke
diagnostics.

For verification, the CSET workflow provides a reproducible and portable
interface to run the MET analysis tools, and visualise the statistics it
produces. This includes things like retrieval of model data and observations,
cycling through different times,

Should I use the workflow or the CLI?
-------------------------------------

The workflow runs the `CSET CLI`_ (Command Line Interface) to produce its
evaluation diagnostics, and provides additional functionality around comparing
models. That doesn't mean you should always use it however. The CLI will be much
faster at returning a single diagnostic, allowing a much more flexible and
responsive analysis where you follow the data. The general workflow will be to
run the workflow to get started, and find interesting phenomena, before using
the CLI to refine your search and quickly probe the underlying physics.

.. _CSET CLI: https://metoffice.github.io/CSET
