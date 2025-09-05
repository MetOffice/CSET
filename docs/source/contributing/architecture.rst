Architecture
============

The architecture of CSET. This page first describes some concepts, then
documents the various workflow apps used, and finally ends with an outline of
where things live in the codebase.

Operators
---------

Recipes
-------

Loaders
-------

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

install_website_skeleton
~~~~~~~~~~~~~~~~~~~~~~~~

Copies static files for the visualisation website to use and creates a symlink
from the configured WEB_DIR to ``$CYLC_WORKFLOW_SHARE_DIR/web``.

This app should probably be merged into finish_website.

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

Runs at the end of the workflow and constructs the index for the visualisation
website from all of the produced diagnostics.

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
