Using git and GitHub
====================

.. attention::

    🚧 Section under construction. 🚧

git clone

Making a branch

Committing your changes

Writing good commit messages:
https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html

Pull Requests
-------------

A pull request is how you submit code for inclusion in CSET. All code changes
must go through a pull request. Pushing directly to the main branch has been
disabled. Before being merged, code will have to go through several stages of
review.

A pull request should generally be a complete feature, and can have as many
commits as needed, as well as being able to be worked on by multiple people. A
new diagnostic chain would be a reasonable level for a pull request, but smaller
ones are also just fine as long as they are "complete". The idea is that the
main branch should always "work", and thus any incomplete or broken
functionality shouldn't be merged in.

.. note::

    Early in development (where we are with CSET as of November 2022) the main
    branch will change hugely very quickly, and CSET doesn't work at all yet,
    and thus pull requests can be much smaller with less stringent requirements
    for merging.

For large features that might taken many months to develop, the main branch may
change too much to merge in the changes cleanly. This can be countered by
rebasing, which is where git reapplies your changes on an up-to-date copy of the
main branch, letting you fix any issues that occur. If you do this regularly
then any fixes should be easy.

A large diagnostic might however be broken out into several pull requests if
there are distinct components. For example, if it needs new operators that could
potentially be used by another diagnostic, then it makes sense to have those
operators in separate pull requests so they can be merged when needed.

Review steps
~~~~~~~~~~~~

There are a number of steps that a pull request has to go through before it can
be merged into the main branch.

The first will be the automatic tests being run by the CI system. This
automatically happens when you make a pull request against the main branch, and
is a good catcher of initial problems. Generally you should resolved any test
failures before asking for code review. The page on :doc:`testing` goes into
more detail.

The next step will be getting other people to look at your code. This involves
three reviews, covering the technical, scientific, and portability aspects of
your submission. A minor change, such as fixing a typo in the documentation,
would only require sign-off from the technical reviewer, and would be a lot
quicker. More detail is on the :doc:`code-review` page.

From the review you will probably receive feedback, and things to change and
improve. Once these points have been addressed the code can be merged into the
main branch, and become part of CSET proper.
