"""Configuration file for the Sphinx documentation builder.

For the full list of built-in configuration values, see the documentation:
https://www.sphinx-doc.org/en/master/usage/configuration.html
"""

from sphinx_gallery.sorting import ExplicitOrder

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "CSET"
copyright = "Crown copyright, Met Office (2022-2026) and CSET contributors."
author = "Met Office and Partners"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx_gallery.gen_gallery",
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

# -- Linkcheck configuration -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-the-linkcheck-builder

linkcheck_anchors = False
linkcheck_ignore = [
    # Ignore GitHub links as we have many and don't want to be rate limited.
    r"https://github.com/.+/(issues|pull)/\d+",
    # GNU.org has an aggressive rate limit.
    r"https://www.gnu.org/software/make/",
    # CSET-restricted-files is a private repository.
    r"https://github.com/MetOffice/CSET-restricted-files",
    # StackOverflow blocks requests.
    r"https://stackoverflow.com/.+",
    # Sourceforge blocks requests.
    r"https://.+\.sourceforge\.io/.+",
    # Met Office internal webserver.
    r"https://wwwspice/.+",
]

# -- Sphinx gallery config ----------------------------------------------------

sphinx_gallery_conf = {
    "plot_gallery": True,
    "examples_dirs": "reference/cset_gallery/examples",  # input scripts
    "gallery_dirs": "reference/cset_gallery/generated",  # output pages
    "filename_pattern": r"\.py$",
    "image_scrapers": ("matplotlib",),
    "thumbnail_size": (800, 600),
    "capture_repr": (),  # disable capture of printed / returned output
    "nested_sections": False,
    "subsection_order": ExplicitOrder(
        [
            "reference/cset_gallery/examples/spatial",
            "reference/cset_gallery/examples/line",
            "reference/cset_gallery/examples/custom",
        ]
    ),
}

suppress_warnings = [
    "toc.not_included",
    "toc.excluded",
]
