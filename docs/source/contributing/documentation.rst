Writing Documentation
=====================

Documentation is essential for any non-trivial project. We therefore need to
write it along side the code, rather than as an afterthought. To make this easy
we will be using the `Sphinx documentation build system`_.

Documentation is written in `reStructuredText`_. This should allow us to
maintain documentation within the version control system, and keep it up to
date. The `Sphinx website`_ has a useful primer to using reStructuredText for
documentation.

The documentation is organised into sections following the `Diátaxis
documentation system`_.

You can build the documentation of CSET with the following commands:

.. code-block:: bash

    # Ensure you are in the docs directory.
    cd docs
    # Build the HTML documentation.
    make html

The documentation will be output to the docs/build/html directory.

.. _Diátaxis documentation system: https://diataxis.fr/

Docstrings
----------

Documentation is also extracted from docstrings in the code. This proximity will
hopefully keep the detailed documentation close to what the code is actually
doing. To give some additional form to the documentation docstrings will be
written in the `NumPy docstring style`_, an example of which is reproduced
below.

.. code-block:: python

    def example_increment_operator(n: float) -> float:
    """
    Increments the input by one.

    Parameters
    ----------
    n: int or float
        The starting number which is incremented.

    Returns
    -------
    int or float
        The result of adding one.

    Raises
    ------
    TypeError
        If n is not a number.

    Notes
    -----
    This is a simple function to demonstrate how they should be generally
    written. It implements addition. [1]_

    The operation of this function is described by the following equation:

    .. math:: n_{final} = n_{initial} + \\int^{1}_{0} \\frac{x}{1} dx

    References
    ----------
    .. [1] Wikipedia contributors, "Addition," Wikipedia, The Free Encyclopedia,
        https://en.wikipedia.org/w/index.php?title=Addition&oldid=1112352709

    Examples
    --------
    >>> Example.example.example_increment_operator(3)
    4
    """
    return n + 1

.. _Sphinx documentation build system: https://www.sphinx-doc.org/
.. _reStructuredText: https://docutils.sourceforge.io/docs/user/rst/quickref.html
.. _Sphinx website: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _NumPy docstring style: https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard
