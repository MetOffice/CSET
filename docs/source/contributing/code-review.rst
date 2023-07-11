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

.. attention::

    🚧 Section under construction. 🚧


Something about the science review…

Portability Review
------------------

.. attention::

    🚧 Section under construction. 🚧


Something about the portability review…
