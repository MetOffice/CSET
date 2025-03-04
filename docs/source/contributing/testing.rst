Automatic Testing
=================

Doing testing more frequently makes it better, as it is much easier to narrow
down what broke. Don't just test when it is time to release. Semi-regular
testing outside of commit CI is useful to test for dependency changes. Regular
testing makes everything better and easier! (especially when automated)

Diagnostic developers should be involved in the testing and the comparison with
KGO, as they know best what is should be outputting. Get diagnostic authors to
take some responsibility in maintaining their diagnostics, rather than it all
being on the release manager will be important for the long term sustainability
of the project.

Having tooling to aid in comparing output to KGO is useful, especially if we
want to get into automated functional testing.

You can run the tests of CSET with the following command:

.. code-block:: bash

    pytest

.. note::

    You will need to make sure you have the conda environment activated, and that
    CSET is installed into it with:

    .. code-block:: bash

        conda activate cset-dev
        pip install -e .

Quick testing of individual components during development
---------------------------------------------------------

Running all test when developing new tests and debugging might take some time.
Fortunately individual tests can be run on the command line with:

.. code-block:: bash

    pytest -k name_of_test


You can also run all of the tests in a file, by giving the name of the file. For
example, the following command will run all of the plotting tests.

.. code-block:: bash

    pytest -k test_plots

Unit Testing
------------

One of the ways we can make CSET much more sustainable is by liberal use of unit
testing.

These consists of small, independent tests that verify that small segments of
code, such as individual functions, are working correctly. They are useful for
verifying algorithms are implemented correctly, and aid maintainability by
narrowing down where problems are.

A unit test will test that a function or method, given specific arguments,
returns the expected result(s). They should be fairly simple, and you will
generally have many. They shouldn't link multiple parts of the code together,
and they shouldn't require much state. If you find that you are writing a
significant amount of code for a test, or want to write helper functions, you
have probably written an integration test instead.

`Some Microsoft recommendation for unit testing (Ignore .NET specific stuff)
<https://learn.microsoft.com/en-us/dotnet/core/testing/unit-testing-best-practices>`_

`Stack Overflow answers giving good overview of unit testing
<https://stackoverflow.com/questions/3258733/new-to-unit-testing-how-to-write-great-tests>`_

Integration Testing
-------------------

Testing of multiple related units, especially around the interaction between
them when they are integrated together. They are very useful for preventing
regressions, and if a bug has previously slipped through testing, another test
should be added to catch it.

They might test several functions that link up to each other, or manipulate the
same data in turn. They are written in generally the same way as unit tests, but
they might require more setup. This is where PyTest fixtures might come in
handy.

Functional Testing
------------------

Testing of larger segments of code, often mimicking an actual use case. This
might be running a workflow, or a similar test that should exercise most of the
code. This is useful for checking if issues have been introduced, but it doesn't
really help narrow down where the issue is.

We may not have the resource to do much automatic functional testing, but it
would be a really nice thing to have.

Documenting Tests
-----------------

.. attention::

    🚧 Section under construction. 🚧


Much like the rest of the codebase, tests need documenting. `This article`_ has
some good points on writing docstrings for unit tests.

.. _This article: https://jml.io/pages/test-docstrings.html

Pre-commit Checks
-----------------

Pre-commit checks are very quick checks to catch any obvious mistakes. They are
usually setup to run automatically when you make a commit. The checks are
installed from .pre-commit-config.yaml, and currently involve formatting python
code, linting, and checking all files are well formed (no trailing whitespace,
etc.).

.. code-block:: bash

    # Ensure your conda environment is activated.
    conda activate cset-dev
    # Install the checks into git
    pre-commit install
