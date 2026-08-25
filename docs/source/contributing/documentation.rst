Writing Documentation
=====================

Documentation is essential for any non-trivial project. We therefore need to
write it along side the code, rather than as an afterthought. To make this easy
we will be using the `Sphinx documentation build system`_.

Documentation is written in `reStructuredText`_. This should allow us to
maintain documentation within the version control system, and keep it up to
date. The `Sphinx website`_ has a useful primer to using reStructuredText for
documentation.

The :ref:`Gallery <gallery>` is generated using `Sphinx-gallery`_.

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


.. _gallery:

Gallery
-------

The `CSET gallery`_ is generated using the `Sphinx-Gallery`_ extension.

Each gallery page follows a similar structure:

* Title and purpose of example.
* Reference section listing the :term:`recipe` used to provide functionality and links to relevant :term:`operator` in :doc:`/reference/operators`.
* Example of requirements for running recipe using ``cset bake`` to generate outputs on the command-line.
* List of configuration options required to enable relevant output via the ``cset_workflow``.
* Minimal python example code to replicate output of ``cset bake`` or workflow settings by directly calling CSET operators inline.
  The python code auto-generates an image file that is captured in the gallery output via `Sphinx-Gallery`_.
  Python codes make use of sample data files.

To add a *new gallery page*, copy any of the existing pages available in a relevant section, and update all details based on the copied template. Examples are available in the following path::

    docs/source/reference/gallery/examples/<name_of_section>/<name_of_example>.py

If the new gallery page should sit in a *new section*, also complete the following steps:

1. Create a new directory ``docs/source/reference/gallery/examples/<name_of_section>``.
2. Add a new file ``docs/source/reference/gallery/examples/<name_of_section>/GALLERY_HEADER.rst`` containing only the title of the section (see existing sections for template).
3. Add new gallery page ``docs/source/reference/gallery/examples/<name_of_section>/<name_of_example>.py``.
4. Update the new ``<name_of_example>.py`` documentation file with relevant details and example working python code.
5. Add ``"reference/gallery/examples/<name_of_section>",`` to the list of gallery subsections in file ``source/conf.py``.

Where possible, reuse any of the existing ``sample_data`` files for new gallery pages.
If needing to generate *new sample_data* to support a new gallery example, add the required file(s) to the following path::

    src/CSET/sample_data

.. note::

    Only small (~10kB) test data files should be added to minimise the overall size of the CSET distribution.

.. _Sphinx documentation build system: https://www.sphinx-doc.org/
.. _reStructuredText: https://docutils.sourceforge.io/docs/user/rst/quickref.html
.. _Sphinx website: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _NumPy docstring style: https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard
.. _CSET gallery: https://metoffice.github.io/CSET/reference/gallery/index.html
.. _Sphinx-Gallery: https://sphinx-gallery.github.io/stable/index.html
