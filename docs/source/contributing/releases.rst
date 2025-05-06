Release Management
==================

Making stable releases is important as it gives everyone something to rally
around, whether developers wanting to get in a certain feature, or users wanting
to find out what has changed.

Scientists like having stable versions to be able to finish their paper with, or
otherwise do their work without things changing.

A release manager will put the release together. Most work for the release
manager is integrating the various pull requests into the mainline. A lot of
work also goes into testing, especially functional testing, where output of the
known version is compared to known good output. A lot of work also goes into
communicating with everyone, such as contributors and changelogs for end users.

For making a release a branch is created with push protection that is
effectively frozen. The relevant commit is also tagged with the release number.
Ideally releases should be mostly automated, as that helps prevent accidents
(like publishing a broken build) happening.

Version numbers are based on `CalVer`_. Specifically they
follow the ``YY.MM.patch`` format, so the first release in February 2024 would
be ``v24.2.0``. Patch releases should only contain bugfixes, and may be released
for older versions, (e.g: ``v24.2.5`` could be released after February). We
should target one feature release a month, so things are not stuck on the trunk
for too long, though quiet periods (e.g: Summer, Christmas) may see a release
missed.

Deprecation policy
------------------

Any change to CSET that removes or significantly alters user-visible behavior
that is described in the CSET documentation will be deprecated for a minimum of
6 months before the change occurs.

Certain changes may be fast tracked and have a deprecation period of 3 months.
This requires at least two members of the CSET team to be in favor of doing so,
and no maintainers opposing.

Deprecation will take the form of a warning being issued by CSET when the
feature is used. Longer deprecation periods, or deprecation warnings for
behavior changes that would not normally be covered by this policy, are also
possible depending on circumstances, but this is at the discretion of the
maintainers.

Note that the documentation is the sole reference for what counts as agreed
behavior. If something isn’t explicitly mentioned in the documentation, it can
be changed without warning, or any deprecation period, in a release. However, we
are aware that the documentation isn’t always complete - PRs that document
existing behavior with the intention of covering that behavior with the above
deprecation process are always acceptable, and will be considered on their
merits.

Python Support Policy
---------------------

CSET follows `NEP 29`_, supporting all python versions released in the prior 42
months.

.. _NEP 29: https://numpy.org/neps/nep-0029-deprecation_policy.html

Making a release
----------------

Making a release is mostly automated. With the use of `setuptools_scm`_ you
don't even need to increment a version number. To create a release you should
use the GitHub web UI. Go to the `Releases`_ page, and press `Draft a new
release`_.

.. image:: release_page.png
    :alt: The GitHub release making page.

On this page you will need to add several things.

* A human readable release title, which should include the version number.
* The target branch to create the release from. (This might be ``main`` most of
  the time.)
* A tag, which should be the version number prefixed with the letter ``v``. For
  example version 24.2.3 should have the tag ``v24.2.3``.
* A description of the changes in the release. Pressing the "Generate release
  notes" button will include the titles of all merged pull requests, which is a
  good starting point, though automated PRs should be removed. It is especially
  important to highlight any changes that might break backwards compatibility.
  The description should also contain links to download CSET from other places.

Once that is all written you simply need to press "Publish release". A release
will be automatically made, and the package will be pushed to PyPI and beyond.

After the release has been made you will want to add the release notes into a
new section in the :doc:`/changelog`. If this is someone's first time
contributing also link their GitHub username to their profile by adding the
following line at the bottom of that section:

.. code-block:: rst

    .. _@username: https://github.com/username


After the release GitHub Action has run (which requires a repository admin to
approve) there are still a few steps left to do:

First update the `conda-forge cset feedstock`_ to publish an updated conda
package. The main change that will need to be made is updating the version and
SHA256 hash in the ``recipe/recipe.yaml`` file. The hash can be obtained from
the `PyPI release page`_ > "Download files" > "View details" on the source
distribution. Once the change is committed it can take up to an hour for the
updated package to become visible via the conda-forge CDN, so you will have to
wait before continuing to the next step.

Once the conda-forge package has updated you will need to update the workflow
lockfiles so the workflow uses new CSET version. This simply requires running
the `update conda lock files GitHub Action`_ and merging the resulting pull
request.

Once that is done you will need to create the workflow tarball to add to the
release. Make a clean checkout of the CSET repository, rename the
``cset-workflow`` directory to ``cset-workflow-v25.X.Y``, and tar it up:

.. code-block:: bash

  tar -czf cset-workflow-v25.X.Y.tar.gz ./cset-workflow-v25.X.Y

Finally edit the release on GitHub and upload the tarball, making sure it is
linked prominently from the release notes.

.. _CalVer: https://calver.org/
.. _Releases: https://github.com/MetOffice/CSET/releases
.. _Draft a new release: https://github.com/MetOffice/CSET/releases/new
.. _setuptools_scm: https://setuptools-scm.readthedocs.io/en/latest/
.. _conda-forge cset feedstock: https://github.com/conda-forge/cset-feedstock
.. _PyPI release page: https://pypi.org/project/CSET/
.. _update conda lock files GitHub Action: https://github.com/MetOffice/CSET/actions/workflows/conda-lock.yml
