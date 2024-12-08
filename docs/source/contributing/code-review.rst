Code Review
===========

Code submitted for inclusion within CSET will have to undergo review on several
fronts. There is the technical review, to ensure it is "good code", it
interfaces well with the rest of the library, has tests and documentation, etc.
Then there is the science review, to ensure it is scientifically correct, and
produces reasonable output. Finally there is the portability review, to make
sure it can work across the systems of the UM partnership.

Technical Review
----------------

The technical review will involve checking the following things:

General review tips
~~~~~~~~~~~~~~~~~~~

Communication is key, especially when done before the review. Early
communication with people who are going to make contributions is important as it
can save having to do a big rewrite of a contribution. Frequent check-ins are
useful to help guide the work and catch issues early. Prior communication
prevents most blocking issues at review.

It is worth taking a step back and considering where contribution fits
conceptually. Often too much focus is placed on issues that are relatively
trivial (coding style, etc.) which while worth fixing, should not distract from
any more fundamental issues or successes around overall design. This article on
the `code review pyramid`_ goes into more detail.

Getting tone across in textual review messages can be difficult, so keep in
impersonal, avoid accusatory or too direct language, and perhaps use emoji or
similar to lighten the mood. 😊 Another good idea is to point out examples of
particularly good code, as it can help foster a more supportive atmosphere.

Checklists and developer guides are really useful, as they allow both reviewer
and reviewee to know what is expected of them. They also help in preventing
things being missed. Having a structured and documented process for reviewing
makes it much more manageable and easier for everyone to follow.

(Met Office specific) The SSE CoP code review exchange is useful for getting
advice on something you don't have experience/expertise with if you encounter it
during a review.

.. _code review pyramid: https://www.morling.dev/blog/the-code-review-pyramid/

Code Style
~~~~~~~~~~

Code should be in a consistent style. Formatting can be enforced automatically
by tools such as black. Many things can be checked automatically by a tool such
as flake8. Some things will need to be checked manually such as variable names
being reasonable and descriptive.

Completeness of Contribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Alongside checking the actual code changes, a technical review should check that
supporting material is also updated. This covers thing like making sure tests
are passing (though this can and should be automated), and making sure tests
have been added/updated to cover new code. It also covers documentation, both
that is has been added and that it is in sufficient detail/accuracy. This may
also seep into the science review for documentation of metrics.


Science Review
--------------

The science review covers many topics in varying levels of detail. The review
should be tailored depending on if it is for plotting functionality or a
diagnostic. The same ethics and standards apply to the science review as the
technical review and for peer-reviewing journal articles.

As with all reviews it requires an impartial approach to reviewing the code. If
you personally do not like a diagnostic that does not mean it should not be
included in CSET. You are not reviewing how good a diagnostic is. Instead you
are reviewing whether the code does what it is supposed to do, how usable the
addition is, and if there is enough information to allow the correct
interpretation of the diagnostic by those new to the diagnostic through the
appropriate use of documentation (docstrings, workflow metadata entry, etc.)
along with journal references where appropriate.

The descriptions of each part of the science review are put in the order they
are recommended to be considered, not necessarily the order of importance. The
idea is to provide comments in the appropriate parts of the code and an overview
as part of the PR discussion.

CSET Documentation
~~~~~~~~~~~~~~~~~~

The documentation should include a short summary statement of what the operator
does, a list of the input parameters, a list of the output, any expected errors
or warnings that it raises and why, notes, references, and clear examples of the
use of the diagnostic. The notes and references are particularly important for
diagnostics and are less of a requirement for plotting operators. The docstrings
of operators that are not prefixed with an underscore are used in the
documentation and so should be considered carefully.

The notes section is the most important section of the documentation for
diagnostics, providing the detail about the diagnostic. It should include a full
description of the diagnostic that includes the logic behind it (including
assumptions used) and, where applicable, make use of appropriate references and
equations. The notes description must include how to interpret the diagnostic
including expected maximum and minimum ranges.

The description can be brief, and if not included it is recommended that a
reviewer asks for a reference pointing to further information if it is available
(e.g. ensure the paper that first describes the diagnostic is cited). The
expected applicability ranges should also be included and cover whether there
are any situations in which the diagnostic will not be sensible to use, or if
the behaviour changes with resolution.

Finally, an interpretation notes or caveats section could be beneficial if there
is likely to be an interpretation of the diagnostic that differs from its
conventional interpretation. For example, does the ordering of the routines
within a model timestep impact the interpretation, e.g., CAPE is traditionally
interpreted before precipitation occurs and so if it is output at the end of the
timestep it will have a different interpretation to if it was output at the
start of the timestep.

Throughout the entire notes section you should be checking for scientific
inaccuracies and whether it can be easily interpreted by another scientist. This
interpretation could be from just reading it as an expert in the area, or with
sufficient referencing for those less familiar with the diagnostic. Ideally, the
extra reading should be kept to a minimum and there would be enough for someone
to be able to interpret the diagnostic but know which papers to cite in a
journal article.

Recipe Documentation
~~~~~~~~~~~~~~~~~~~~

This type of documentation is particularly important for plotting. The
descriptions provided in the recipe should be sufficient to allow interpretation
of the diagnostic, or plot, for those that have not used/seen it before.

These descriptions will be included in the output webpage. Therefore, important
information to include will be the maximum/minimum ranges, the interpretation
and applicability ranges of the diagnostic. For some plots (e.g., q-q plots)
this should include a general "how to interpret" section which covers what
patterns to look for to identify certain relationships or factors. This should
mimic those parts from the CSET documentation.

Further applicability considerations should include assumptions and caveats with
the chain of operators used and how that could impact the results, e.g. impact
of re-gridding. And if any operators could break assumptions of the diagnostics
and thus have applicability ranges (e.g. resolution supported by the
diagnostic).

GUI Documentation
~~~~~~~~~~~~~~~~~

The GUI documentation should be checked for usability. Important questions to
ask are whether there is enough information provided that a new user to CSET
could "pick it up" and run it with limited input from the developers. If
specific example files or default file locations are required these should be
clearly specified in the description.

It is also worth considering the parts of the documentation that would be more
beneficial in the "help" or "description" sections, with the latter being
readily visible in the GUI. For example, any specific input requirements should
be in the description, including the required format.  Any important caveats,
assumptions and applicability information should be mentioned in the GUI
extended help text.

Code
~~~~

The code review can overlap with the technical review. However, the main focus
of the science code review is to make sure the scientific logic of the code
follows the principles of the diagnostic. For example, if someone is coding a
diagnostic based on an equation:

* Is the equation correct?
* Has it been sensibly coded (broken down into appropriate terms in necessary)?
* Have the correct conditionals been applied?
* Are there any missing terms?
* Are the units correct?

Ultimately, does the code produce what you would expect it to from a science
perspective, is it easily understood and debugged, and are there suitable
comments in the code?

Plotting Routines
~~~~~~~~~~~~~~~~~

For a plotting routine, specific questions to consider include:

* Does the plot make sense (e.g. is the vertical coordinate plotted on the
  y-axis; does it improve the interpretation if a logarithmic scale is used)?
* Is the plot easy to interpret or is guidance required and is that guidance
  appropriate?
* Are the colour bars appropriate and mindful of accessibility if a specific
  colour bar is required?
* Is the labelling present and appropriate?
* Is the plot legible?

Portability Review
------------------

.. attention::

    🚧 Section under construction. 🚧

Something about the portability review…
