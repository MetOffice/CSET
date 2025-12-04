Why use CSET?
=============

Evaluation of weather and climate models requires an assessment of model
characteristics, and the ability to understand what drives them. This typically
involves comparing different models (whether physics-based or machine learned,
or hybrid approaches) to each other and to a variety of observations across a
range of model diagnostics. For model development, there is a requirement to
assess the impacts of different model configurations and choices on results.
Evaluation is an iterative process, and each step can unveil more questions
that leads to a need for deeper investigation.

CSET aids in this by providing a flexible way to interrogate model and
observational data, using diagnostics that can be quickly created by the
combination of operators in :doc:`operator recipes </usage/operator-recipes>`.
Common operations such as reading, writing, and regridding are provided to
reduce duplication of effort.

CSET provides a legacy for user-developed evaluation methods and diagnostics to
be shared and documented, with :doc:`well-defined working practices and review
processes</contributing/index>`. It aims to embed and share best practice for
evaluation and verification of weather and climate models using observational
data. CSET primarily targets higher resolution atmosphere model processes
(i.e. convective-scale with grid-spacing of order km's and turbulence-scale
with sub-km grid spacing) on regional to global domains across weather and
climate timescales. CSET provides flexibility to provide consistent evaluation
of physics-based or machine learning approaches, and to compare these directly.

CSET provides many benefits to users and developers, including:

* Embeds and shares best practice for evaluation and verification of weather and climate models using observational data.
* A legacy for user-developed evaluation methods and diagnostics to be shared and documented, with :doc:`well-defined working practices and review processes</contributing/index>`.
* A route for contributors to CSET to ensure legacy of newly developed diagnostics, to ensure benefit to wider weather and climate modelling communities.
* Reproducibility, portability, accessibility, maintainability, and quality assurance of evaluation tools to support a range of applications.

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
