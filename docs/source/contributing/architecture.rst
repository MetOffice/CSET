Architecture
============

The architecture of CSET. This page first describes some concepts, then
documents the various workflow apps used, and finally ends with an outline of
where things live in the codebase.

Operators
---------

Operators provide the core functionality of CSET. Each operator is a function
that takes some input and returns some output, in some cases producing plots.

All of the operators in CSET are contained in modules in
``src/CSET/operators/``, which group related operators. For example ``plot.py``
contains various plotting operators.

Recipes
-------

To produce a diagnostic, operators must be combined in recipes, which
are YAML files containing a graph of operators to execute, along with
any needed arguments and some metadata providing the diagnostic's title,
description and broad category.

The included recipes in CSET can be found in ``src/CSET/recipes/``.

A recipe may optionally contain variables, such as ``$VARIABLE``, which is
replaced by a value provided on the command line or by a loader.

Loaders
-------

Loaders load recipes for use in the workflow, filling in any variables from the
configuration provided in the ``rose-suite.conf``.

The included loaders in CSET can be found in ``src/CSET/loaders/``.

Workflow
--------

To enable large scale running of CSET we provide a cylc workflow. The workflow's
source can be found in ``src/CSET/cset_workflow/``, with its logic being defined
in the ``flow.cylc`` file.

This workflow has three main aims:

1. Fetching the model and observation data.
2. Running all of the enabled recipes on that data.
3. Building a visualisation website for the produced diagnostics.

These aims are accomplished by a series of rose-apps that are run as part of the
workflow. These apps live in ``src/CSET/cset_workflow/app/``.

validate_environment
~~~~~~~~~~~~~~~~~~~~

A small shell script that checks the conda environment has been loaded correctly
and that the ``cset`` command line is available at the start of the workflow.

assign_model_colours
~~~~~~~~~~~~~~~~~~~~

Runs at the start of the workflow to assign each model a colour, so that
different line plots and such can use consistent colours for each model. The
colours are assigned into a style file which is used when baking the recipes.

fetch_fcst
~~~~~~~~~~

Runs for each model/obs source on each cycle to retrieve the required data. It
can switch between different implementations for different data sources, such as
the filesystem or HTTP.

parbake_recipes
~~~~~~~~~~~~~~~

Runs for each cycle. Reads the user configuration and the writes out all the
enabled recipes with their variables filled in. This allows them to be "baked"
(run) in parallel.

bake_recipes
~~~~~~~~~~~~

Runs for each cycle, and additionally as bake_aggregation_recipes in the final
cycle. This takes the parbaked recipes and runs them to produced the desired
diagnostics.

This will be that task that takes the majority of the workflow's runtime, and is
the only one that needs significant compute resource.

Internally it runs the ``cset bake`` command line for each recipe in parallel
using `rose_bunch`_, however to allow the baked recipes to be decided at runtime
the first thing that runs is the ``baker.sh`` script, which writes out the list
of recipes to bake as a rose optional configuration, and then run the rose app
using it.

.. _rose_bunch: https://metomi.github.io/rose/doc/html/api/built-in/rose_bunch.html

finish_website
~~~~~~~~~~~~~~

Runs at the end of the workflow and creates the visualisation website.

It copies static files for the website to use, constructs the index of the
produced diagnostics, and creates a symlink from the configured WEB_DIR to
``$CYLC_WORKFLOW_SHARE_DIR/web``.

housekeeping
~~~~~~~~~~~~

Deletes the retrieved data at the end of the workflow to free up disk space.

send_email
~~~~~~~~~~

Sends a notification email to the workflow owner letting them know the workflow
is complete.

Other apps
~~~~~~~~~~

The following apps aim to integrate METplus in the workflow but are not currently used:

* demo_pointstat
* metplus_ascii2nc
* metplus_grid_stat
* metplus_point_stat

Code outline
------------

The code of CSET lives in the ``src/CSET/`` directory, arranged as follows:

src/CSET
~~~~~~~~

.. code-block:: text

    src/CSET
    ├── cset_workflow                  # Detailed below for clarity.
    ├── loaders
    │   ├── __init__.py                # Imports all loaders for the rest of CSET.
    │   └── ...                        # Then lots of loaders, as described above.
    ├── operators
    │   ├── __init__.py                # Code for executing ("baking") recipes.
    │   ├── _colorbar_definition.json  # Default colourbar definitions.
    │   ├── _plot_page_template.html   # Template for diagnostic output page.
    │   ├── _stash_to_lfric.py         # Mapping between STASH codes and LFRic variable names.
    │   ├── _utils.py                  # Common utility code for operators.
    │   └── ...                        # Then lots of operators, as described above.
    ├── recipes
    │   ├── __init__.py                # Code for parbaking recipes.
    │   └── ...                        # Then lots of recipes, as described above.
    ├── __init__.py                    # CLI entrypoint. Logging setup, argument parsing, etc.
    ├── __main__.py                    # Allows running `python -m CSET`.
    ├── _common.py                     # Common utility code.
    ├── extract_workflow.py            # Implementation of `cset extract-workflow`.
    └── graph.py                       # Implementation of `cset graph`.

src/CSET/cset_workflow
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    src/CSET/cset_workflow
    ├── app                          # Contains the rose apps described above.
    │   ├── assign_model_colours
    │   │   ├── bin
    │   │   │   └── assign_model_colours.py  # Executable for app.
    │   │   └── rose-app.conf        # Rose app configuration. Mostly sets the executable.
    │   └── ...                      # Lots more rose apps in here.
    ├── bin                          # Files in bin are automatically on the workflow's PATH.
    │   └── app_env_wrapper          # Wrapper script to run things in the conda environment.
    ├── lib                          # Available for import into cylc's jinja2 templating.
    │   └── python
    │       └── jinja_utils.py       # A couple helper functions used in flow.cylc.
    ├── meta                         # Validation and GUI layout for user configuration.
    │   ├── diagnostics
    │   │   └── rose-meta.conf       # Diagnostic configuration.
    │   ├── rose-meta.conf           # Automatically generated file, don't edit.
    │   └── rose-meta.conf.jinja2    # Workflow configuration.
    ├── opt                          # Pre-made configurations for consistent evaluation.
    │   └── rose-suite-RAL3LFRIC.conf
    ├── site                         # Site-specific cylc configuration.
    │   └── localhost.cylc
    ├── flow.cylc                    # Workflow definition detailing how tasks are run.
    ├── install_restricted_files.sh  # Script for installing site-specific files.
    ├── README.md
    ├── rose-suite.conf              # User configuration of workflow and diagnostics.
    └── rose-suite.conf.example      # Blank user configuration to be copied.
