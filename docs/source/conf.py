"""Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "CSET"
copyright = "Crown copyright, Met Office (2022-2025) and CSET contributors."
author = "Met Office and Partners"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_baseurl = "https://metoffice.github.io/CSET/"

# -- LaTeX output configuration ----------------------------------------------
# https://www.sphinx-doc.org/en/master/latex.html

latex_engine = "xelatex"
latex_elements = {"papersize": "a4paper"}
latex_show_urls = "footnote"

# -- Extlinks configuration --------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html

extlinks = {
    "issue": ("https://github.com/MetOffice/CSET/issues/%s", "Issue #%s"),
    "pr": ("https://github.com/MetOffice/CSET/pull/%s", "PR #%s"),
}

# Ignore GitHub links as we have many and don't want to be rate limited.
linkcheck_ignore = [
    r"https://github.com/.+/(issues|pull)/\d+",
]
