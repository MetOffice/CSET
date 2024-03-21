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

Create a branches
-----------------

You can directly create the respective code branch from the issues on the GitHub
code repository pages, or from the git CLI.

Check-out code
--------------

Follow instructions to download CSET code. You should have a directory called
``CSET``.

In ``CSET`` switch to your development branch and check it out.

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

Recipes use ``yaml`` format and step through a combination of existing and new
operators to built a diagnostic. Existing operators are documented in the
:doc:`/reference/index`.

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

Add recipe into CSET workflow
-----------------------------

This procedure will be simplified in the future. At the moment recipes are
included in two locations. Once in the ``cset-workflow/includes`` directory and
once in the ``src/CSET/recipes`` directory. This way we can run recipes with the
`cset bake` command as well as running them through the CSET workflow.

- Include recipe in a `cylc` include file into
  ``cset-workflow/includes/<new_operator_include_file>.cylc``

- Add ``<new_operator_include_file.cylc>`` to ``flow.cylc``

- ``meta/rose-meta.conf``: to add section for toggle button to allow selection
  of new recipe file

- ``opt/rose-suite-niwa.conf``: add option for new recipe using name  used in
  ``flow.cylc``

- ``rose-suite.conf.example``: add option for new recipe

- ``rose-suite.conf``: add option for new recipe

Built recipe into CSET CLI
--------------------------

.. note::

    This step will be simplified in future and instead the include file will
    link to the recipe directory.

Adding a recipe in the CSET CLI enables running individual diagnostics
recipes on the command line with the `cset bake` command and without running the
whole workflow. This is a useful step for testing new operators or recipes
during development.

Now we are linking the  ``src/CSET/recipes/<new_recipe_name.yml>``. The
steps in this file should be identical to the steps in the
``CSET-workflow/includes/<new_operator_include_file.cylc>``.

- ``src/CSET/operators/__init__.py``: include operator into  import line

- ``pyproject.toml``: include any external python package dependencies

- ``requirements/environment.yml`` include any external python package
  dependencies

Test your code
--------------

Tests can be run by invoking the ``tox`` command and are also run on ``git
commit``.

- for running test type

.. code-block:: bash

    tox

- in case of a failed test the testing environment autocorrects some issues such
  as whitespace trailing and typos and modifies files.

  - Check changed files with

.. code-block:: bash

    git status

  - If agreeing with change then add to staging area with

.. code-block:: bash

    git add <filename>

- commit changes to local staging area with

.. code-block:: bash

    git commit

Committing code
---------------

- Committing into local repository

.. code-block:: bash

    git commit

- If message ``Changes not staged for commit`` then need to add changed files to
  staging areas using

.. code-block:: bash

    git add <filename>

- Repeat git commit command and log commit message

- If automatically running tests flag error, resolve them, repeat ``git add``
  and ``git commit`` steps. Typos and simple errors are automatically resolved
  and can be added with

.. code-block:: bash

    git status
    git add <changed filenames>
    git commit

Pushing code into remote repository
-----------------------------------

- push code into remote repository branch with:

.. code-block:: bash

    git push --set-upstream origin <insert branch name>

- ``git push`` will help you and give you options

- list of branches

.. code-block:: bash

    git branch

- if remote branch is behind changes on trunk then update remote branch on
  github repository by merging in changes form main

- in local branch pull remote changes in

.. code-block:: bash

    git branch --set-upstream-to=origin <local branch name>

- rebase the local branch

.. code-block:: bash

    git pull --rebase

- Due to rebase you now need to force a push to the head of your remote branch

.. code-block:: bash

    git push -f origin HEAD

Start the review process
------------------------

Request reviewer on GitHub page under pull requests.

.. _recipe file: https://metoffice.github.io/CSET/usage/operator-recipes
