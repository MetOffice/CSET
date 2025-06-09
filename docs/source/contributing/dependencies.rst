Dependencies
============

Requirements of a new dependency
--------------------------------

Dependencies should be sufficiently maintained before being added to CSET. This
is typically observed through recent and regular activity on the source
repository, especially from multiple people. The dependency should be adding a
valuable capability to justify the potential cost of us having to maintain or
replace it in future.

Finally dependencies must be published under an open source licence that is
compatible with CSET's, and be distributed via conda-forge.

Adding a new dependency
-----------------------

While a single ``conda install <package>`` can be used to experiment with an
additional dependency, to properly include it in CSET it needs to be added to a
number of files.

Specifically it needs to be added to the ``pyproject.toml`` under the
"dependencies" key, and ``requirements/environment.yaml`` under the appropriate
dependencies section.

After updating those two files and making a pull request, you'll need to rerun
the conda lockfile generation action. In `Actions > Update conda lock files >
Run workflow`_ select your branch, then run the workflow. A new PR will be
created to update the lockfiles, which you can merge into your own branch.

.. _Actions > Update conda lock files > Run workflow: https://github.com/MetOffice/CSET/actions/workflows/conda-lock.yml

Updating the conda-forge package
--------------------------------

Conda packages are built from "feedstocks", which are repositories that contain
the list of steps to build, package, and test the package, as well as the
required metadata, such as the package name, and needed dependencies.

The CSET feedstock is at `github.com/conda-forge/cset-feedstock`_. The only user
editable file in this repository is `recipe/recipe.yaml`_. All of the other
files are either automatically generated from the recipe file, or are inert
things that don't affect the resultant package, like the README.

In this case we care about the runtime dependencies in `recipe/recipe.yaml`_:

    `Lines 27 to 37 in commit 805148a`_:

    .. code-block:: yaml

        run:
        - python >=${{ python_min }}
        - numpy
        - iris >=3.12.2
        - ruamel.yaml >=0.17
        - pygraphviz >=1.11
        - mo_pack >=0.3
        - isodate >=0.6
        - markdown-it-py >=3.0
        - nc-time-axis
        - iris-grib

Because this repository is not within the MetOffice GitHub organisation, we
cannot directly change it. We have to make a `fork of the repository`_ to make
changes. Once you have created a fork, you can edit the feedstock recipe and
make the needed changes. In this case we need two changes.

1. Add the new dependency under the runtime requirements section. Remember to
   use the conda-forge package name!

   .. code-block:: yaml

       requirements:
         run:
           - my_dependency

2. Increase the `build number`_. This is used when the package version does not
   increase, so conda knows which version is more up-to-date.

Finally make your pull request, the `feedstock maintainer`_ will review and merge
it, and soon after your updated package will be published on conda-forge.

.. _github.com/conda-forge/cset-feedstock: https://github.com/conda-forge/cset-feedstock
.. _recipe/recipe.yaml: https://github.com/conda-forge/cset-feedstock/blob/main/recipe/recipe.yaml
.. _Lines 27 to 37 in commit 805148a: https://github.com/conda-forge/cset-feedstock/blob/805148a2191e1256667fb74f8e5b051f6339af56/recipe/recipe.yaml#L27-L37
.. _fork of the repository: https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo
.. _build number: https://github.com/conda-forge/cset-feedstock/blob/805148a2191e1256667fb74f8e5b051f6339af56/recipe/recipe.yaml#L14
.. _feedstock maintainer: https://github.com/conda-forge/cset-feedstock?tab=readme-ov-file#feedstock-maintainers
