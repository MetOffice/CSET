Documentation Practices
=======================

Documentation is essential for any non-trivial project. We therefore need to
write it along side the code, rather than as an afterthought. To make this easy
we will be using the `Sphinx documentation build system`_ as it is very good.

Documentation is written in `reStructuredText`_. This should allow us to
maintain documentation within the version control system, and keep it up to
date. The `Sphinx website`_ has a primer to using reStructuredText for
documentation.

Documentation is also going to be extracted from docstrings in the code. This
proximity will hopefully keep the detailed documentation close to what the code
is actually doing. to give some additional form to the documentation docstrings
will be written in the `NumPy docstring style`_.

.. _Sphinx documentation build system: https://www.sphinx-doc.org/
.. _reStructuredText: https://docutils.sourceforge.io/docs/user/rst/quickref.html
.. _Sphinx website: https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html
.. _NumPy docstring style: https://numpydoc.readthedocs.io/en/latest/format.html#docstring-standard
