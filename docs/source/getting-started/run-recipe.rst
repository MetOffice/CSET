Run a pre-existing recipe
=========================

.. Tutorial on running a pre-existing recipe, covering cset bake.

CSET works by running recipes that describe how to transform and and visualise
data. It comes with a collection of pre-written recipes to get you started. In
this tutorial you will use CSET to plot the mean surface air temperature of a
forecast.

We will create a basic spatial plot of the mean surface air temperature, using a
pre-existing recipe. Download the following linked recipe:
:download:`air_temperature_spatial_plot.yaml`

Now you need to find some data to process. Download the following linked example
file: :download:`air_temp.nc`

Now we are ready to run our recipe. This is where we use the ``cset bake``
command. This takes the input data file, an output path and the recipe file. The
output should be a directory, but it will be created if it does not exist.

.. code-block:: bash

    cset bake -i air_temp.nc -o output/ -r air_temperature_spatial_plot.yaml

This will run the recipe and leave its output in the specified output directory.
You can look at the visualised output with ``xdg-open output/index.html``.

You've now successfully run CSET with a pre-existing recipe. In :doc:`the next
tutorial <visualise-recipe>` we will see what is going on inside.
