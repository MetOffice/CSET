Add a new diagnostic
====================

In CSET diagnostics are defined as a collections of steps in a `recipe file`_.

New built-in recipes should be added to the CSET CLI, then added as include
files into the includes/ directory of the workflow. They should then be added to
meta/rose-meta.conf so they appear in rose edit, and flow.cylc, so they are
included in the workflow.

Custom recipes should be directly included in include files. They should be
saved to the environment variable ``CSET_RECIPE``. Similarly they should then be
added to the flow.cylc, but this is something that will be improved in future.

Step-by-Step quick start guide to including a diagnostic via a recipe into CSET
and building a new operator:

Open issues
-----------

Open a new issue on the CSET repository and assign yourself. It can be helpful
to @mention any other interested parties to discuss the design at this stage.

Check-out code branch
---------------------

Follow the :ref:`instructions to download the CSET code <getting-the-code>`. You
should have a directory called ``CSET``.

Inside the ``CSET`` directory switch to your development branch.

.. code-block:: bash

    git switch -c "<your branch name here>"

Keep up to date with code changes
---------------------------------

While you are developing your code ensure to pull remote changes into your local
repository:

.. code-block:: bash

    git pull

Build operators
---------------

Build one or several operators and include them as python files in directory.
You can group similar operators in the same file.

.. code-block:: bash

    src/CSET/operators/<new_operator>.py

Build recipe
------------

Recipes step through a combination of existing and new operators to built a
diagnostic. Existing operators are documented in the :doc:`/reference/index`.
The recipe syntax is documented in :doc:`/reference/recipe-format`.

Operators can be nested into each other in each operator step in the recipe to
pass their output as constraint or input into another operator.

Each operator step passes their output cube as input into the next operator step
automatically.

Include the recipe in directory ``src/CSET/recipes/<new_recipe_name>.yaml``.

Build a test
------------

Create a unit test for each new operator.

Include test function into ``tests/operators/test_<new_operator>.py``.

Ensure *not to upload large test data* when committing changes by omitting them
from git add command. Instead of adding all changes using ``git add .`` please
add the changes explicitly to avoid adding test files and data files using

.. code-block:: bash

    git add <insert filename>

You can check for changed file names with

.. code-block:: bash

    git status

Built recipe into CSET CLI
--------------------------

.. note::

    This step will be simplified in future and instead the include file will
    link to the recipe directory.

Adding a recipe in the CSET CLI enables running individual diagnostics recipes
on the command line with the `cset bake` command and without running the whole
workflow. This is a useful step for testing new operators or recipes during
development.

Now we are linking the ``src/CSET/recipes/<new_recipe_name.yml>`` into
the cset command line program.

* ``src/CSET/operators/__init__.py``: include operator module into import line
  and ``__all__`` list.
* ``pyproject.toml``: include any new python package dependencies
* ``requirements/environment.yml`` include any new python package dependencies

Add recipe into CSET workflow
-----------------------------

This procedure will be simplified in the future. At the moment recipes are
included in two locations. Once in the ``cset-workflow/includes`` directory and
once in the ``src/CSET/recipes`` directory. This way we can run recipes with the
`cset bake` command as well as running them through the CSET workflow.

* Create a Cylc include file at
  ``cset-workflow/includes/<new_operator_include_file>.cylc``, copying an
  existing include file for inspiration.
* ``meta/rose-meta.conf``: to add section for toggle button to allow selection
  of new recipe file.
* ``rose-suite.conf.example``: add option for new recipe.
* Add option to ``rose-suite.conf`` to test for yourself.


Test your code
--------------

Tests can be run by invoking the ``pytest`` command. Some additional checks are
also run on ``git commit`` via ``pre-commit``. To run the tests:

.. code-block:: bash

    pytest

Committing code
---------------

Commit into local repository

.. code-block:: bash

    git commit

If message ``Changes not staged for commit`` then need to add changed files to
the staging areas using

.. code-block:: bash

    git add <filename>

Repeat git commit command and log commit message

If automatically running tests flag error, resolve them, repeat ``git add`` and
``git commit`` steps. Some typos and simple errors are automatically detected
and resolved, and can then be added with:

.. code-block:: bash

    git status
    git add <changed filenames>
    git commit

Pushing code into remote repository
-----------------------------------

Push code into remote repository branch with:

.. code-block:: bash

    # Just "git push" will suggest the correct command.
    git push --set-upstream origin <insert branch name>

If the remote branch is behind changes on trunk then you update the remote
branch on the GitHub repository by merging in changes from main. While on your
branch:

.. code-block:: bash

    # Merge in the changes from the copy of main on GitHub.
    git merge origin/main

Don't forget to push your changes back up to GitHub.

.. code-block:: bash

    git push

Start the review process
------------------------

Make a :ref:`pull-request` on GitHub to propose your changes for inclusion in
the trunk.

Once you have satisfied the steps in the :doc:`/contributing/index` go ahead and
request a review on GitHub.

.. _recipe file: https://metoffice.github.io/CSET/usage/operator-recipes
