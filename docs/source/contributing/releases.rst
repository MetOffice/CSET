Release Management
==================

Making stable releases is important as it gives everyone something to rally
around, whether developers wanting to get in a certain feature, or users wanting
to find out what has changed. Scientists like having stable versions to be able
to finish their paper with, or otherwise do their work without things changing
underneath them.

A release manager will put the release together. Most work for the release
manager is integrating the various pull requests into the mainline. A lot of
work also goes into testing, especially functional testing, where output of the
known version is compared to known good output. A lot of work also goes into
communicating with everyone, such as contributors and changelogs for end users.

Version numbers are based on `CalVer`_. Specifically they follow the
``YY.MM.patch`` format, so the first release in February 2024 would be
``v24.2.0``. Patch releases should only contain bugfixes, and may be released
for older versions, (e.g: ``v24.2.5`` could be released after February). We
target one feature release every couple months, so things are not stuck on the
trunk for too long, though quiet periods (e.g: Summer, Christmas) may see a
release missed.

Deprecation policy
------------------

Any change to CSET that removes or significantly alters user-visible behavior
that is described in the CSET documentation will be deprecated for a minimum of
6 months before the change occurs.

Certain changes may be fast tracked and have a faster deprecation period.
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

CSET follows `SPEC 0`_, supporting all python versions released in the prior
three years.

.. _SPEC 0: https://scientific-python.org/specs/spec-0000/

Making a release
----------------

To make a CSET release a maintainer should follow these steps.

First you should ensure you have all the changes you want to be included in the
release merged into the main branch. This will be the main factor determining
when you can cut a release.

Once all the changes are in, manually test a fresh clone of the main branch to
ensure there are no breaking issues. A good method is to go through the
:doc:`Getting Started Tutorials </getting-started/index>` and make sure they all
work.

With that tested we are happy with the content of our release and it is time to
document it by writing our changelog.

#. Within the ``docs/source/changelog.rst`` file create a new heading for the release
   containing the release number and the date.

#. Create the list of changes since the last release. This can be automatically
   generated from pull request titles by running the following script::

      # Print out merged PRs since last release in correct format.
      gh pr list \
        --repo MetOffice/CSET \
        --search "is:pr state:merged merged:>$(git log -1 --format='%cs' $(git tag --list 'v*' --sort 'version:refname' | tail -1))" \
        --limit 300 --json number,title,author \
        --template '{{range .}}{{if not .author.is_bot}}* {{.title}} by `@{{.author.login}}`_ in :pr:`{{.number}}`{{"\n"}}{{end}}{{end}}' \
        | tac

   Once generated go through this list and improve any titles that are missing
   details or are not formatted sensibly.

#. If any new contributors have joined add a "New Contributors" section after
   the list of pull requests calling them out and link their GitHub username.
   New contributors will be flagged as warnings when you build the
   documentation. The new contributor section should look like this::

      New Contributors:

      * `@example`_ made their first contribution in :pr:`1`

      .. _@example: https://github.com/example

#. Finally write a few paragraphs highlighting the most important user-facing
   changes in the release. It is especially important to highlight any changes
   that might break backwards compatibility. These paragraphs should be placed
   before the list of pull requests.

   Once finished the changelog entry should look something like this::

      YY.M.N (20YY-MM-DD)
      -------------------

      A few paragraphs summarising the most important changes in the release.

      * Fix an annoying bug by `@example`_ in :pr:`1`
      * Add a cool new feature by `@example`_ in :pr:`2`

      New Contributors:

      * `@example`_ made their first contribution in :pr:`1`

      .. _@example: https://github.com/example

#. Commit the release notes into a new pull request and get it reviewed and
   merged into the ``main`` branch. No other pull requests should be merged
   before this one, as otherwise you will have to update the release notes
   again.

#. Now create a draft release on GitHub. To create a release you should use the
   GitHub web UI. Go to the `Releases`_ page and press `Draft a new release`_.

   .. image:: release_page.png
       :alt: The GitHub release making page.

   On this page you will need to add several things.

   * A new tag, which should be the version number prefixed with the letter ``v``.
     For example version 24.2.3 should have the tag ``v24.2.3``.
     **Make sure your tag is correct, as it cannot be changed once published.**
   * The target branch/commit to create the release from. This will be ``main``
     most of the time, unless you are creating a patch release for a previous
     version.
   * The release title, which should start with the tag and optionally include a
     human readable release name.
   * A description of the changes in the release and links to download CSET from
     other places. This should follow this template with the summary paragraphs
     copied from the changelog::

       <REPLACE WITH RELEASE SUMMARY PARAGRAPHS>

       There are many more fixes and improvements. Please visit [metoffice.github.io/CSET/changelog](https://metoffice.github.io/CSET/changelog) for the full details.

       [PyPI package](https://pypi.org/project/CSET/) | [conda-forge package](https://anaconda.org/conda-forge/cset) | [Documentation](https://metoffice.github.io/CSET/)

   Then press "Save draft" to save this release as a draft.

#. Go to the `CSET-restricted-files repository`_ and create a new branch from
   ``main`` named ``releases/vXX.Y``, matching the first two numbers of the tag.
   For example, CSET v24.2.3 should have a restricted branch named
   ``releases/v24.2``.

   This branch is picked up by ``cset install-restricted-files`` and prevents
   new changes to the restricted files from breaking older versions of CSET.

#. Check over your draft release. Especially **ensure you check the tag and
   target branch are correct**, as they cannot be changed after the release is
   published.

#. Once checked, press "Publish release" to create the immutable release. This
   triggers a release GitHub Action which will automatically build and upload
   the package to PyPI.

#. Finally we need to update the `conda-forge cset feedstock`_ to publish an
   updated conda package. This should be done from an up-to-date fork of the
   feedstock repository, per the `conda-forge maintaining packages
   documentation`_.

   The main change that will need to be made is updating the version and SHA256
   hash in the ``recipe/recipe.yaml`` file. The hash can be obtained from the
   `PyPI release page`_ > "Download files" > "View details" on the source
   distribution. If the dependencies of CSET have changed you will also need to
   update them.

   Once the change is committed and merged to the ``main`` branch of the
   feedstock repository it can take up to an hour for the updated package to
   become visible via the conda-forge CDN, but no further action is required.

#. Once the release is available you should communicate it to users so the know
   they can use it. This include on internal channels as well as via public
   ones.

.. _CalVer: https://calver.org/
.. _Releases: https://github.com/MetOffice/CSET/releases
.. _Draft a new release: https://github.com/MetOffice/CSET/releases/new
.. _setuptools_scm: https://setuptools-scm.readthedocs.io/en/latest/
.. _CSET-restricted-files repository: https://github.com/MetOffice/CSET-restricted-files
.. _conda-forge cset feedstock: https://github.com/conda-forge/cset-feedstock
.. _PyPI release page: https://pypi.org/project/CSET/
.. _update conda lock files GitHub Action: https://github.com/MetOffice/CSET/actions/workflows/conda-lock.yml
.. _conda-forge maintaining packages documentation: https://conda-forge.org/docs/maintainer/updating_pkgs/#example-workflow-for-updating-a-package
