Run a pre-existing recipe
=========================

.. Tutorial on running a pre-existing recipe, covering cookbook and bake.

CSET works by running recipes that describe how to transform and and visualise
data. It comes with a collection of pre-written recipes to get you started. In
this tutorial you will use CSET to plot the mean surface air temperature of a
forecast.

We will create a basic spatial plot of the mean surface air
temperature. There is a pre-existing recipe for this that can be retrieved with
the CSET cookbook command.

Try the following:

.. code-block:: bash

    cset cookbook

This will write out a recipes folder containing recipe ``.yaml`` files to your
current directory. We will use the
``mean_surface_air_temperature_spatial_plot.yaml`` recipe.

Now you need to find some data to process. You can `download an example file
here`_, or with the following command.

.. code-block:: bash

    curl -LO https://github.com/MetOffice/CSET/raw/main/tests/test_data/air_temp.nc

Now we are ready to run our recipe. This is where we use the ``cset bake``
command. This takes the input data file, an output path and the recipe file. The
output should be a directory, but it will be created if it does not exist.

.. code-block:: bash

    cset bake air_temp.nc output/ recipes/mean-air-temp-spacial-plot.yaml

This will run the recipe and leave its output in the specified output directory.

The most interesting output will be the plot, which you can look at with
``xdg-open output/plot.svg``.

You've now successfully run CSET with a pre-existing recipe. In the next
tutorial we will see what is going on inside.

.. _download an example file here: https://github.com/MetOffice/CSET/raw/main/tests/test_data/air_temp.nc
