Community Seamless Evaluation Toolkit (CSET) Documentation
==========================================================

.. toctree::
   :hidden:

   CSET Documentation <self>
   getting-started/index
   usage/index
   reference/index
   background/index
   contributing/index
   changelog
   GitHub <https://github.com/MetOffice/CSET>

The **Community Seamless Evaluation Toolkit, CSET**, is a community-developed open
source toolkit for evaluation, verification, and investigation of weather and
climate models. It supports the evaluation of physical numerical models, machine
learning models, and observations seamlessly across time and space scales. CSET
primarily targets, but is not limited to, high-resolution atmospheric processes,
from convective to turbulence scales (i.e. kilometre to sub-kilometre grid
spacing), across regional or global domains.

Useful links
------------

`Source Code`_ | `Issue Tracker`_ | Releases_ | `Discussion Forum`_

For information on how to use CSET, see :doc:`getting-started/index`.

For information on getting involved as a developer, see
:doc:`contributing/index`.

.. _Source Code: https://github.com/MetOffice/CSET
.. _Issue Tracker: https://github.com/MetOffice/CSET/issues
.. _Releases: https://github.com/MetOffice/CSET/releases
.. _Discussion Forum: https://github.com/MetOffice/simulation-systems/discussions/categories/cset-toolkit

Overview of CSET
----------------

CSET provides a centralised and peer-reviewed set of tools to aid
process-oriented verification and evaluation for UM, LFRic, and machine learning
models, supporting both deterministic and ensemble configurations.

At the Met Office and Momentum® Partnership CSET supports parametrisation
development, diagnostic development and evaluation research. It is integral to
the Regional Atmosphere and Land (RAL) model development process for the Unified
Model and LFRic atmospheric modelling codes.

CSET is designed to be continuously evolving and improving, driven by community
inputs. Support for verification and evaluation of a range of machine learning
models is expected to grow, alongside use of observations from an increasing
range of sources to support evaluation. It will utilise the Model Evaluation
Tools (MET) software to provide a range of verification metrics aligned with
operational verification best practices. Where relevant, CSET will provide
interfaces to utilise other evaluation packages to support particular evaluation
requirements.

For model and diagnostics developers, CSET offers:

* Well-documented, tested, and peer-reviewed evaluation tools.
* Flexible evaluation code that can adapt to user needs.
* Traceable and reproducible results during a model development and assessment cycle.
* Community development through open access and agreed working practices.
* Access to bespoke observations for diagnostics.
* A legacy for diagnostics through continued maintenance and improved discoverability.
* Portability across sites, including :doc:`easy installation </getting-started/installation>`.

For information on how to use CSET, see :doc:`getting-started/index`.

For information on getting involved as a developer, see
:doc:`contributing/index`.

Use the side bar to the left to access other pages of the documentation.

Key Principles of CSET
----------------------

Community
    Evaluation software developed for and by a wide network of model development and
    evaluation scientists, enabling common approaches to distributed evaluation activities.

Seamless
    Supporting assessment, evaluation, verification and understanding of physical and
    machine learning models as well as observations across time and space scales, and from regional to global application.

Evaluation
    Providing a process-oriented focus to model assessment, supporting depth of
    comparison between different model configurations and assessment relative to a range of observations.

Toolkit
    A flexible software including code, recipes, diagnostics and workflow to manage a range of
    user requirements, underpinned by modern software development practices.

Code of Conduct
---------------

All contributors to CSET must follow the `Met Office Simulation Systems Code of
Conduct`_.

.. _Met Office Simulation Systems Code of Conduct: https://metoffice.github.io/simulation-systems/FurtherDetails/code_of_conduct

Licence
-------

© Crown copyright, Met Office (2022-2025) and CSET contributors.

Licensed under the Apache License, Version 2.0 (the "License"); you
may not use this file except in compliance with the License. You may obtain a
copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed
under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR
CONDITIONS OF ANY KIND, either express or implied. See the License for the
specific language governing permissions and limitations under the License.
