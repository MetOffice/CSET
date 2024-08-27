Run a pre-existing recipe
=========================

.. Tutorial on running a pre-existing recipe, covering cset bake.

CSET works by running recipes that describe how to transform and and visualise
data. It comes with a collection of pre-written recipes to get you started. In
this tutorial you will use CSET to plot the mean surface air temperature of a
forecast.

We will create a basic spatial plot of the mean surface air temperature, using a
pre-existing recipe. You can `download the recipe file here`_.

Now you need to find some data to process. You can `download an example file
here`_, or with the following command.

.. code-block:: bash

    # Download recipe file.
    curl -LO https://gist.githubusercontent.com/jfrost-mo/6e539d5be20bfa28342bf4ff82f24dea/raw/air_temperature_spatial_plot.yaml
    # Download example data.
    curl -LO https://github.com/MetOffice/CSET/raw/main/tests/test_data/air_temp.nc

Now we are ready to run our recipe. This is where we use the ``cset bake``
command. This takes the input data file, an output path and the recipe file. The
output should be a directory, but it will be created if it does not exist.

.. code-block:: bash

    cset bake -i air_temp.nc -o output/ -r air_temperature_spatial_plot.yaml

This will run the recipe and leave its output in the specified output directory.

The most interesting output will be the plot, which you can look at with
``xdg-open output/plot.png``.

You've now successfully run CSET with a pre-existing recipe. In the next
tutorial we will see what is going on inside.

.. _download the recipe file here: https://gist.githubusercontent.com/jfrost-mo/6e539d5be20bfa28342bf4ff82f24dea/raw/air_temperature_spatial_plot.yaml
.. _download an example file here: https://github.com/MetOffice/CSET/raw/main/tests/test_data/air_temp.nc
