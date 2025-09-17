---
title: "CSET: Toolkit for evaluation of weather and climate models"
tags:
  - Python
  - Cylc
  - Weather
  - Climate
  - Atmospheric Science
authors:
  - name: James Frost
    orcid: 0009-0009-8043-3802
    affiliation: 1
  - name: James Warner
    orcid:
    affiliation: 1
  - name: Sylvia Bohnenstengel
    orcid:
    affiliation: 1
  - name: David Flack
    orcid:
    affiliation: 1
  - name: Huw Lewis
    orcid:
    affiliation: 1
  - name: Dasha Shchepanovska
    orcid:
    affiliation: 1
  - name: Jon Shonk
    orcid:
    affiliation: 1
  - name: Bernard Claxton
    orcid:
    affiliation: 1
  - name: Jorge Bornemann
    orcid:
    affiliation: 2
  - name: Carol Halliwell
    orcid:
    affiliation: 1
  - name: Magdalena Gruziel
    orcid:
    affiliation: 3
  - name: Pluto ???
    orcid:
    affiliation: 4
  - name: John M Edwards
    orcid:
    affiliation: 1
affiliations:
  - name: Met Office, United Kingdom
    index: 1
    ror: 01ch2yn61
  - name: NIWA, New Zealand
    index: 2
    ror: 01ch2yn61
  - name: Interdisciplinary Centre for Mathematical and Computational Modelling, Poland
    index: 3
  - name: Centre for Climate Research Singapore, Meteorological Service Singapore, Singapore
    index: 4
    ror: 025sv2d63
date: 17 September 2025
bibliography: paper.bib
---

# CSET: Toolkit for evaluation of weather and climate models.

<!-- TODO: Recopy paragraphs from Word doc, as it is still being updated. -->

## Summary

<!-- A summary describing the high-level functionality and purpose of the software for a diverse, non-specialist audience. -->

The Convective- [and turbulence-] Scale Evaluation Toolkit (**CSET**) is an open source library, command line tool, and workflow for evaluation of weather and climate models. It can analyse model and observational data and visualises the output in a website to allow the development of a coherent evaluation story for numerical weather prediction, climate, and machine learning models across time and spatial scales.

## Statement of need

<!-- A Statement of need section that clearly illustrates the research purpose of the software and places it in the context of related work. -->

Evaluating weather and climate models is essential for the model development process and has applications in various research domains. Typically, an evaluation includes both context and justification to demonstrate the benefit of model changes compared to other models or previous model versions. The verification provides the context or baseline for understanding the model’s performance through comparison against observation. The evaluation then demonstrates the benefit through comparison against theoretical expectations or previous or different version of the model and other models for similar application areas using diagnostics derived from model output to explain the context.

Historically, evaluation has typically been done with bespoke scripts. These scripts are rarely portable, and the results of evaluation at different institutions are therefore difficult to compare. The writing of these scripts for each evaluation takes significant effort, and they are often poorly maintained, with little in the way of testing or documentation.

## Contribution to the field

The toolkit aims to cater for the full evaluation process, providing a range of verification diagnostics and diagnostics derived from model output that allow for both process-based and impact-based understanding. The verification side of CSET utilises the Model Evaluation Tools (METplus) verification system [@metplus] to provide a range of verification metrics that are aligned with operational verification best practices. The justification side of CSET consists of a range of diagnostics derived from model output. The diagnostics include process-based diagnostics for specific phenomena. Impact-based diagnostics that can be used to provide meaning to changes for customers are also included.

The diagnostics within CSET are well-documented, tested, and peer reviewed, allowing confidence for users and increased discoverability. Furthermore, CSET provides a legacy for diagnostics via a clear maintenance infrastructure. The documentation covers diagnostic applicability allowing for confidence in their use. By building around composable operators CSET’s evaluation code can be adapted to user needs while maintaining traceability, putting customers at the heart of evaluation.

Technically, CSET has been built with portability in mind. It can run on a range of platforms, from laptops to supercomputers, and can be easily installed from conda-forge. It is built on a modern software stack that is underpinned by Cylc (a workflow engine for complex computational tasks) [@cylc8], Python 3, Iris (a Python library for meteorological data analysis) [@iris], and METplus (a verification system for weather and climate models). The toolkit is open source and actively developed in the open on GitHub, with extensive automatic unit and integration testing. It aims to be a community-based toolkit, thus contributing to CSET is made easy and actively encouraged with clear developer guidelines to help.

## Research usage

<!-- Mention (if applicable) a representative set of past or ongoing research projects using the software and recent scholarly publications enabled by it. -->

In the Met Office and across the Momentum® Partnership (a cooperative partnership of institutions sharing a seamless modelling framework for weather and climate science and services) [@momentum_partnership], CSET has been the tool of choice for understanding the regional configuration of the next-generation numerical weather prediction and climate model LFRic. [@lfric] It has helped us to characterise the regional configuration and lead to improvements in our model.

## Related software packages

<!-- TODO: Discuss alternatives, such as ESMValTool. -->

## Acknowledgements

<!-- Acknowledgement of any financial support. -->

We acknowledge contributions and support from the Met Office and Momentum® Partnership for this project.

## References

<!-- A list of key references, including to other software addressing related needs. Note that the references should include full names of venues, e.g., journals and conferences, not abbreviations only understood in the context of a specific discipline. -->

* @metplus
* @cylc8
* @iris
* @momentum_partnership
* @lfric
