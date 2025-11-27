CSET Documentation
==================

.. toctree::
   :hidden:

   self
   getting-started/index
   usage/index
   reference/index
   background/index
   contributing/index
   changelog
   GitHub <https://github.com/MetOffice/CSET>

Key Principles of CSET
----------------------

**Community**: Evaluation software developed for and by a wide network of model development and
evaluation scientists, enabling common approaches to distributed evaluation activities.
**Seamless**: Supporting assessment, evaluation, verification and understanding of physical and
machine learning models as well as observations across time and space scales, and from regional to global application.
**Evaluation**: Providing a process-oriented focus to model assessment, supporting depth of
comparison between different model configurations and assessment relative to a range of observations.
**Toolkit**: A flexible software including code, recipes, diagnostics and workflow to manage a range of
user requirements, underpinned by modern software development practices.

Overview of CSET
----------------

CSET, the Community Seamless Evaluation Toolkit, is
a community-developed open-source toolkit for the seamless evaluation, verification
and investigation
of weather and climate models. It supports the evaluation of physical numerical models and machine learning models
as well as observations seamlessly across time and space scales. CSET primarily targets,
but is not limited to, higher resolution atmosphere model processes (i.e. convective-scale
with grid-spacing of order km's and turbulence-scale with sub-km grid spacing) on regional
to global domains.

CSET provides a centralised and peer-reviewed source of tools to aid
process-oriented evaluation for UM, LFRic physical and machine learning models, supporting both
deterministic and ensemble configurations.

CSET is designed to be continuously evolving and improving, driven by community inputs.
Support for verification and evaluation of a range of machine learning models is expected
to grow, alongside use of observations from an increasing range of sources to support
evaluation. It will utilise the Model Evaluation Tools (MET) software to provide a
range of verification metrics aligned with operational verification best practices.
Where relevant, CSET will provide interfaces to utilise other evaluation packages to
support particular evaluation requirements.

CSET is closely aligned to parametrisation development, diagnostic development and
evaluation research in the Met Office and Momentum® Partnership, serving as an
integral part of the Regional Atmosphere and Land (RAL) model development process
focussed on the Unified Model and LFRic atmosphere model codes.

- For CSET model and diagnostics developers, CSET offers:
   - Well-documented and peer-reviewed evaluation tools.
   - Community development through open access and agreed working practices.
   - A clearly defined release cycle.
   - Automatic testing.
   - Flexible evaluation code that can adapt to user needs.
- CSET is built with portability in mind and can be run on:
   - Local desktops.
   - HPC systems.
   - Cloud servers.
- CSET ensures:
   - Traceable and reproducible results during a model development and assessment cycle.
   - Diagnostics access to observations.
   - A legacy through continued maintenance and improved discoverability.
- CSET is built using a modern software stack, underpinned by
   - python3,
   - iris and
   - METplus.

Contributions to CSET are promoted by clear documentation and working practices,
automatic testing, and an open access GitHub code base.

For information on how to use CSET, see :doc:`getting-started/index`.

For information on getting involved as a developer, see
:doc:`contributing/index`.

Use the side bar to the left to access other pages of the documentation.

Useful Links
------------

`Source Code`_ | `Issue Tracker`_ | Releases_ | `Discussion Forum`_

.. _Source Code: https://github.com/MetOffice/CSET
.. _Issue Tracker: https://github.com/MetOffice/CSET/issues
.. _Releases: https://github.com/MetOffice/CSET/releases
.. _Discussion Forum: https://github.com/MetOffice/simulation-systems/discussions/categories/cset-toolkit

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
