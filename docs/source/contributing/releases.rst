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

Backwards Compatibility Policy
------------------------------

As soon as we have users for CSET maintaining a certain level of backwards
compatibility becomes important, as they will want their use of CSET to continue
to work in future. As such it is useful to define a backwards compatibility
policy that sets expectations about the way backwards incompatible (AKA
"breaking") changes are made.

Some things to consider:

* How quickly backwards incompatible changes can be made.
* How long deprecation periods should be for different sizes of change.
* How the changes will be communicated with users.
* Guidance on avoiding making backwards incompatible changes where possible.

Making a Release
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

Once that is all written you simply need to press "Publish release". A release
will be automatically made, and the package will be pushed to PyPI and beyond.

.. _CalVer: https://calver.org/
.. _Releases: https://github.com/MetOffice/CSET/releases
.. _Draft a new release: https://github.com/MetOffice/CSET/releases/new
.. _setuptools_scm: https://setuptools-scm.readthedocs.io/en/latest/
