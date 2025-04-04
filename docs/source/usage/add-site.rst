Add a new site for the CSET workflow
====================================

While the localhost site can be used for basic running on a single computer,
sites with a compute cluster will want to setup the CSET cylc workflow to take
advantage of it. This will involve the following steps:

1. Add site file at cset-workflow/site/<site>.cylc
2. Add entry to cset-workflow/meta/rose-meta.conf.jinja2
3. Select site in rose edit.

In this example we will add the site configuration for the fictional ACME
Corporation.

Add site file
-------------

First thing we need to add is a cylc include file to set the default compute
platform for tasks within the CSET workflow. For ACME Corp. we are going to
create a new file at ``cset-workflow/site/acme.cylc`` with the following
content:

.. code-block:: ini

    # Site file for ACME Corporation.
    [runtime]
        [[root]]
        platform = acme-cluster
            [[[directives]]]
            --mem = 2000
            --ntasks = 2

This file is a snippet of cylc code that sets up the basic environment upon
which tasks will run. It sets the ``root`` runtime environment, which all other
tasks will inherit from.

The most important line is ``platform = acme-cluster``, which sets the job
platform that intensive tasks will be submitted to. This will be a site-specific
value that comes from your global cylc configuration. You can list your site's
available platforms with:

.. code-block:: bash

    cylc config --platform-names

The directives control the default resource allocation for the tasks. Most
intensive tasks in CSET will override these, so the default specified here can
remain as a fairly modest allocation with a couple gigabytes of memory.

If required you can also define additional workflow changes in this file, that
will overwrite CSET's flow.cylc file. If you need to make additional changes
please `open an issue on the CSET GitHub repository`_, so we can ensure your use
case is supported directly in CSET.

Add rose edit metadata entry for site
-------------------------------------

With the site file created we now need to add our site to the rose
configuration. This requires editing the metadata at
``cset-workflow/meta/rose-meta.conf.jinja2``. Within that file find the
definition for the SITE variable, and add your site to it. This requires adding
a value that matches the filename (without the ``.cylc`` extension) of your site
file, as well as a value title that is the display name of your site. For ACME
we will adjust it as follows:

.. code-block:: diff

     [template variables=SITE]
     ns=Setup
     title=Site
     description=Which institution to load the site-specific configuration for.
     help=The site-specific configuration should live in a file under site/
         For example the Met Office configuration lives under "site/metoffice.cylc".

         Localhost does not use any site-specific settings, and should work on any
         cylc installation. It will however run on the scheduler server.
    -values="localhost", "metoffice", "niwa"
    +values="localhost", "metoffice", "niwa", "acme"
    -value-titles=Localhost, Met Office, NIWA
    +value-titles=Localhost, Met Office, NIWA, "ACME Corp."
     compulsory=true
     sort-key=aaa

This file is a template, so after changing and saving it we will need to
regenerate the actual rose metadata file. There is a pre-commit hook installed
for this, so it can be done with:

.. code-block:: bash

    pre-commit run --all-files

Select site in rose edit
------------------------

The final step is to select our site to use. This can be done in rose edit, at
the top of the Setup tab. Alternatively the rose-suite.conf can be modified
directly with your site's value:

.. code-block:: text

    SITE="acme"

With that saved you are now ready to run the CSET workflow for your site.

Upstreaming configuration
-------------------------

Once you are happy with your site-specific configuration you may want to save it
to a central location for easy reuse by others using CSET at your site. There
are three options of where to store it, from most preferred:

1. The `main CSET GitHub repository`_.
2. The Momentum Partnership restricted `CSET site-specific config repository`_.
3. Locally at your site.

If you don't mind your site-specific configuration being public the preferred
location is the `main CSET GitHub repository`_. This ensures your configuration will be
distributed with all future versions of CSET, and requires no special access.
Simply follow the :doc:`Developer's Guide </contributing/getting-started>` to
add your site file.

If you would prefer to keep your site-specific configuration non-public, and are
a Momentum Partnership member, we have a designated `CSET site-specific config
repository`_ that contains these configurations for various Momentum Partners.
It is this repository that is installed via the ``install_restricted_files.sh``
script. Even when your file remains restricted like this you should still
contribute your rose metadata changes to the `main CSET GitHub repository`_ so
your site shows up as an option to users.

Finally if neither of the above locations are suitable you can simply
redistribute your site-specific configuration file within your organisation, and
have users manually copy it into the workflow's site directory.

.. _main CSET GitHub repository: https://github.com/MetOffice/CSET
.. _CSET site-specific config repository: https://github.com/MetOffice/CSET-workflow
.. _open an issue on the CSET GitHub repository: https://github.com/MetOffice/CSET/issues
