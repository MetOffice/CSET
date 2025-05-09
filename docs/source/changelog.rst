Changelog
=========

.. Each release has its own section structured as follows:
    Title: version (release date)
    Short prose summary of most important changes.
    List of changes with who made them and a link to the PR.

.. Unreleased
.. ----------

.. Add changes here, probably taken from GitHub release notes.
.. Highlight any user facing changes. E.g:
.. "* `@gh-user`_ did foo to bar in :pr:`9999`. This enables baz."

25.5.0 (2025-05-02)
--------------------

Amongst the many changes in this release we now have the capability to plot
multiple models on the same plot, at least for histogram plots. This should be a
significant aid to those comparing multiple models with CSET. We also have
significantly improved documentation (though it has been online for a while),
improved colour bars, various performance improvements, simplification of
workflow configuration GUI, and various bug fixes.

* Update workflow CSET package by `@jfrost-mo`_ in :pr:`1291`
* Ignore codespell error for "runN" by `@jfrost-mo`_ in :pr:`1292`
* Update output image in full cylc example tutorial by `@jfrost-mo`_ in :pr:`1293`
* Add fully worked example with CYLC to documentation by `@jwarner8`_ in :pr:`1213`
* include precipitation specific colorbar and unit conversion by `@Sylviabohnenstengel`_ in :pr:`1268`
* Improve colorbar formatting to reduce whitespace by `@ukmo-huw-lewis`_ in :pr:`1296`
* Nicer output on crash from run_cset_recipe by `@jfrost-mo`_ in :pr:`1262`
* Normalise all LFRic coord names by `@jfrost-mo`_ in :pr:`1299`
* Add option to skip writing output by `@jfrost-mo`_ in :pr:`1277`
* Updated default colorbar definition for radiation by `@ukmo-huw-lewis`_ in :pr:`1305`
* Conditionally fix times in callbacks to avoid corrupting dates by double fixing by `@jfrost-mo`_ in :pr:`1297`
* Avoid writing meta.json outside tempdir during test by `@jfrost-mo`_ in :pr:`1311`
* Retry failed processing tasks by `@jfrost-mo`_ in :pr:`1313`
* Add SKIP_WRITE to example configuration by `@jfrost-mo`_ in :pr:`1320`
* Update cset-workflow GUI organisation with clearer labelling for "General setup", "Cycling and Models", diagnostic-type and evaluation-type specific option panels by `@ukmo-huw-lewis`_ in :pr:`1310`
* Drop support for python 3.10 by `@jfrost-mo`_ in :pr:`1316`
* Add last few changes into v25.3.1 changelog by `@jfrost-mo`_ in :pr:`1288`
* Add preprocessing task to speed up workflow by `@jfrost-mo`_ in :pr:`1301`
* Add model level support to CSET by `@jwarner8`_ in :pr:`1270`
* Refactor lfric_time_callback by `@jfrost-mo`_ in :pr:`1321`
* Simplify cset-workflow plot options and env variable names by `@ukmo-huw-lewis`_ in :pr:`1319`
* Move diagnostic archive creation into bake by `@jfrost-mo`_ in :pr:`1326`
* Provide input paths via recipe variables and remove unneeded ``cset recipe-id`` command by `@jfrost-mo`_ in :pr:`1329`
* Update logic for reading SKIP_WRITE environment variable when running cset-workflow by `@ukmo-huw-lewis`_ in :pr:`1339`
* Correctly format print-based logging in run_cset_recipe.py by `@jfrost-mo`_ in :pr:`1341`
* Fix implementation of grid latitude grid longitude callback for non rotated pole inputs by `@ukmo-huw-lewis`_ in :pr:`1340`
* Remove unnecessary array construction in radtime_prehour callback by `@jfrost-mo`_ in :pr:`1342`
* Add category to transect recipe by `@jfrost-mo`_ in :pr:`1348`
* Symbolic link to raw filesystem data to avoid slow copy by `@jfrost-mo`_ in :pr:`1352`
* Add additional STASH to LFRic mappings by `@jfrost-mo`_ in :pr:`1354`
* Plot all models on a single histogram plot by `@refszkentla`_ in :pr:`1324`. This was their first contribution 🎉
* Order LFRic before UM in RAL3-LFRic rose config by `@jfrost-mo`_ in :pr:`1349`
* Add v25.5.0 release notes and document more of the release process by `@jfrost-mo`_  in :pr:`1357`
* Fix formatting of v25.3.1 release notes by `@jfrost-mo` in :pr:`1358`
* Add last v25.5.0 release notes by `@jfrost-mo` in :pr:`1359`

New Contributors

* `@refszkentla`_ made their first contribution in :pr:`1324`

.. _@refszkentla: https://github.com/refszkentla

25.3.1 (2025-03-27)
-------------------

A smaller release contains a number of bug fixes and other minor improvements
ahead of a new feature release next month. The most noticeable change maybe be
the plot colorbar now being horizontal to leave more space for titles and
side-by-side comparisons.

* Remove unneeded deletion from housekeeping by `@jfrost-mo`_ in :pr:`1241`
* Add conda HTTP error to common errors by `@jfrost-mo`_ in :pr:`1242`
* Reduce PROCESS time limit to 15 minutes by `@jfrost-mo`_ in :pr:`1243`
* Getting started documentation improvements by `@jfrost-mo`_ in :pr:`1218`
* Check for staggered grid with name rather than STASH in difference operator by `@jfrost-mo`_ in :pr:`1248`
* Fully sort website index by `@jfrost-mo`_ in :pr:`1249`
* Increase aggregation wallclock to 3 hours by `@jfrost-mo`_ in :pr:`1250`
* Skip running dummy tasks by `@jfrost-mo`_ in :pr:`1120`
* Document adding a site-specific configuration by `@jfrost-mo`_ in :pr:`1251`
* Avoid calling ``os.sync()`` by `@jfrost-mo`_ in :pr:`1276`
* Avoid accessing non-captured output in MASS fetch script by `@jfrost-mo`_ in :pr:`1278`
* Correct for instances where longitude plot bounds caused set_extent to by `@ukmo-huw-lewis`_ in :pr:`1283`
* 1-line change to move default position of map colorbars to horizontal by `@ukmo-huw-lewis`_ in :pr:`1284`
* Overwrite partially downloaded files from MASS by `@jfrost-mo`_ in :pr:`1281`
* Add release notes for v25.3.1 by `@jfrost-mo`_ in :pr:`1286`

25.3.0 (2025-03-06)
-------------------

This release is the baseline for evaluating **RAL3-LFRic#708.1** with RMED
Ticket #708 detailing the science configuration. It introduces a fixed
evaluation functionality for RAL3-LFRic and RAL3-UM, new functionality, bug
fixes, and improvements. Key features for RAL3-LFRic evaluation include:

* Surface fields: spatial plots, timeseries, histograms, model comparison plots,
  time aggregation by hour of day, validity time, forecast range, area averages.
* Pressure level fields: spatial plots, timeseries, histograms, model
  comparison plots, time aggregation by hour of day, validity time, forecast
  range, area averages, vertical profiles, PDFs.

Additional capabilities: transects, point selection, QQ plots, age of air
diagnostics, cape diagnostics that can be selected by the user.

The next release will add analysis on model levels, multi-line plotting, and
more derived variables.

* Upload hidden coverage files to fix GitHub Actions breakage by `@jfrost-mo`_ in :pr:`832`
* Pin GitHub Actions to specific commits to prevent random breakage by `@jfrost-mo`_ in :pr:`846`
* Switch to data time cycling to support multiple models and multiple case studies or trials by `@jfrost-mo`_ in :pr:`765`
* Note that all documentation shell examples use bash by `@jfrost-mo`_ in :pr:`861`
* Add colorbar entries for more standard names by `@jfrost-mo`_ in :pr:`839`
* Support python 3.13 and remove usage of tox in CI by `@jfrost-mo`_ in :pr:`872`
* Correct execute_recipe docstring; it takes an input directory by `@jfrost-mo`_ in :pr:`869`
* Fix colorbar min and max not being set on pcolormesh plots by `@jfrost-mo`_ in :pr:`870`
* Error fetch_fcst task when no data found for a model, as it usually indicates a typo in the data path by `@jfrost-mo`_ in :pr:`842`
* Rewrite colorbar loading to use default colorbar definition from inside CSET package by `@jfrost-mo`_ in :pr:`871`
* Fix spelling of stratiform_rainfall_rate in colorbar definition by `@jfrost-mo`_ in :pr:`878`
* Improve transect title by `@jwarner8`_ in :pr:`829`
* Update colorbar definitions by `@daflack`_ in :pr:`892`
* Fix typo in comment by `@jfrost-mo`_ in :pr:`906`
* Sort conda lock files to aid reviewing by `@jfrost-mo`_ in :pr:`890`
* Explicitly use conda-forge conda channel for updating conda and resolving lock files by `@jfrost-mo`_ in :pr:`886`
* Exclude `__main__.py` from test coverage measurement by `@jfrost-mo`_ in :pr:`880`
* Remove HTTP status check as urlopen already does it by `@jfrost-mo`_ in :pr:`882`
* Test templating variables into recipe parser by `@jfrost-mo`_ in :pr:`881`
* Test recipe listing and detailing functions by `@jfrost-mo`_ in :pr:`883`
* Fix type signature by `@jwarner8`_ in :pr:`931`
* Changes to fix longitude convention to be in the range -180 degrees to 180 degrees where possible by `@JKPShonk`_ in :pr:`896`
* Disable strict checking that TLS certificates are well formed by `@jfrost-mo`_ in :pr:`904`
* Change CSET introduction on documentation welcome page by `@Sylviabohnenstengel`_ in :pr:`899`
* Harmonise variable names from UM Stash to LFRic variable and long_name by `@ukmo-huw-lewis`_ in :pr:`898`
* Add date to cset plot menu items by `@mo-sanamahmood`_ in :pr:`934`
* Wrap plot title and increase figure size by `@Sylviabohnenstengel`_ in :pr:`935`
* Fix supported arg type in regrid operator by `@jwarner8`_ in :pr:`948`
* Use non-interactive backend for plotting by `@jfrost-mo`_ in :pr:`951`
* Update to WEB_ADDR documentation by `@daflack`_ in :pr:`955`
* Add iris-grib library support by `@jwarner8`_ in :pr:`960`
* Revert "Add iris-grib to dev dependencies" by `@jfrost-mo`_ in :pr:`974`
* Import CSET.recipes as recipes during testing for readability by `@jfrost-mo`_ in :pr:`968`
* Add nicer error messages for unhandled exceptions by `@jfrost-mo`_ in :pr:`884`
* Target lockfile update PR to source branch by `@jfrost-mo`_ in :pr:`963`
* Convert CLI interface tests to not use `subprocess.run` by `@jfrost-mo`_ in :pr:`970`
* Use regular install for CI tests by `@jfrost-mo`_ in :pr:`463`
* Add age of air diagnostic functionality by `@jwarner8`_ in :pr:`480`
* Add mask operators by `@daflack`_ in :pr:`967`
* Documentation update for mask operator by `@daflack`_ in :pr:`990`
* Adds spatial perturbation operator by `@daflack`_ in :pr:`979`
* New callbacks to standardise some dim names by `@jwarner8`_ in :pr:`983`
* Fix location of AOA docs by `@jwarner8`_ in :pr:`1001`
* Fix no title in surface histogram plots by `@jwarner8`_ in :pr:`1006`
* Updates generate_levels_constraint documentation for ensemble functionality by `@daflack`_ in :pr:`1003`
* Log cubes that don't merge in `load_cube` operator by `@jfrost-mo`_ in :pr:`1022`
* Remove unneeded `name` global attribute by `@jfrost-mo`_ in :pr:`1024`
* Adds DKE functionality by `@daflack`_ in :pr:`1002`
* Format JSON when writing by `@jfrost-mo`_ in :pr:`1041`
* Limit domain statistics to 3 s.f. and move below plot by `@jfrost-mo`_ in :pr:`1040`
* Require tasks to succeed in DEBUG mode by `@jfrost-mo`_ in :pr:`1039`
* Generalise spatial plot log message by `@jfrost-mo`_ in :pr:`1042`
* Separate words in callback function name with _ so it is easier to read by `@jfrost-mo`_ in :pr:`1043`
* Handle sorting files outside the current directory in `sort_json.py` script by `@jfrost-mo`_ in :pr:`1046`
* Replace all remaining usage of typing.Union with `|` by `@jfrost-mo`_ in :pr:`1047`
* Fix typo in rose-edit help by `@jfrost-mo`_ in :pr:`1051`
* Add configuration file for GitHub Issue templates by `@jfrost-mo`_ in :pr:`1035`
* Merge lead time into initiation time cycling by `@jfrost-mo`_ in :pr:`1053`
* Add utility function for equalising attributes by `@jfrost-mo`_ in :pr:`1052`
* unify colourbar for relative_humidity between UM and LFRic by `@Sylviabohnenstengel`_ in :pr:`1038`
* unify colourbar for cloud_base_altitude between um and lfric by `@Sylviabohnenstengel`_ in :pr:`1059`
* Reduce useless log messages by `@jfrost-mo`_ in :pr:`1045`
* Adds collapse_by_hour_of_day operator by `@daflack`_ in :pr:`1034`
* Sort colorbar JSON files via pre-commit hook by `@jfrost-mo`_ in :pr:`1060`
* Handle CubeList in line plotting operator by `@Sylviabohnenstengel`_ in :pr:`954`
* Ensure multiple cases are put into a single cube by `@daflack`_ in :pr:`1050`
* Data loading improvements, including loading multiple models by `@jfrost-mo`_ in :pr:`1054`
* Improve rose edit and simplify include files by `@jfrost-mo`_ in :pr:`1055`
* Collapse by validity time by `@daflack`_ in :pr:`1067`
* Update collapse_by_hour for multiple cases by `@daflack`_ in :pr:`1068`
* Accept microsecond precision in iris times by `@jfrost-mo`_ in :pr:`1074`
* Parallelise CI tests by `@jfrost-mo`_ in :pr:`1071`
* Use "spawn" start method for multiprocessing by `@jfrost-mo`_ in :pr:`1075`
* Fix issue with rose-suite.conf variable by `@jwarner8`_ in :pr:`1082`
* Remove unnecessary computation from age-of-air test by `@jfrost-mo`_ in :pr:`1081`
* Share multiprocessing pool across ensemble members by `@jfrost-mo`_ in :pr:`1080`
* Add data fetching script from MASS by `@jfrost-mo`_ in :pr:`1084`
* Spatial difference plots by `@jfrost-mo`_ in :pr:`1061`
* Make MASS fetch data script executable by `@jfrost-mo`_ in :pr:`1085`
* Add additional colour bar definitions from UKEP Plot by `@jfrost-mo`_ in :pr:`1064`
* Increase default memory to 4G for processes by `@jwarner8`_ in :pr:`1090`
* Relax shape check in difference plots by `@jwarner8`_ in :pr:`1088`
* Deduplicate an unlimited amount of STASH warnings by `@jfrost-mo`_ in :pr:`1091`
* Search for correct log_record in fetch_data tests by `@jfrost-mo`_ in :pr:`1089`
* Implement required return value for MASSFileRetriever by `@jfrost-mo`_ in :pr:`1095`
* Use CSET read operator to load test data, and improve various fragile tests by `@jfrost-mo`_ in :pr:`1076`
* Remove housekeep_raw task from workflow by `@jfrost-mo`_ in :pr:`1104`
* Allow `collapse.collapse` to handle a CubeList by `@jfrost-mo`_ in :pr:`985`
* Update workflow for single recipe case aggregation by lead time by `@daflack`_ in :pr:`1086`
* Update workflow to allow case aggregation by hour of day by `@daflack`_ in :pr:`1101`
* Updates workflow for aggregation by validity time by `@daflack`_ in :pr:`1102`
* Handle CubeLists in `plot_vertical_line_series` and `plot_scatter_plot` by `@Sylviabohnenstengel`_ in :pr:`1100`
* Add dummy tasks to prevent workflow graph failures by `@jfrost-mo`_ in :pr:`1119`
* Update rose-suite.conf.example by `@jfrost-mo`_ in :pr:`1121`
* Fix for pressure coordinate name variants plus enforce units to be hPa by `@jwarner8`_ in :pr:`1106`
* Fix issue where pressure coordinate returns Unit object, not str by `@jwarner8`_ in :pr:`1123`
* Allow real-world coordinates to be specified in single-point timeseries by `@cehalliwell`_ in :pr:`943`
* Extend histogram plot with CubeList handling capability by `@Sylviabohnenstengel`_ in :pr:`1116`
* switch off auto-scale for x axis to avoid jumping of ticks on x axis … by `@Sylviabohnenstengel`_ in :pr:`1134`
* Various fixes and new recipes for pressure level functionality by `@jwarner8`_ in :pr:`1127`
* Switch web viewer to sidebar layout by `@jfrost-mo`_ in :pr:`1132`
* Tidy Conf by making aggregatable collapsible, and fill missing example values by `@jwarner8`_ in :pr:`1135`
* Histogram enhancements by `@jwarner8`_ in :pr:`1137`
* Fix LFRic time coordinate metadata by `@jwarner8`_ in :pr:`1117`
* Shrink sidebar font size by `@jfrost-mo`_ in :pr:`1142`
* Various QuickLook fixes and enhancements of surface plot functionality by `@jwarner8`_ in :pr:`1122`
* put in colorbar for surface_net_shortwave_flux_difference by `@BernardClaxton`_ in :pr:`1138`
* Fix spelling in plot.py by `@jfrost-mo`_ in :pr:`1147`
* Search for all varnames and allow user colorbar override by `@jfrost-mo`_ in :pr:`1141`
* Support flexible pressure_level dependent colorbars by `@Sylviabohnenstengel`_ in :pr:`1140`
* Fill out colorbar definitions for missing variables by `@BernardClaxton`_ in :pr:`1145`
* Unify .gitignore to cover both workflow and library by `@jfrost-mo`_ in :pr:`1151`
* Update environments used throughout CSET to python 3.13 by `@jfrost-mo`_ in :pr:`1153`
* Run generate_rose_meta script as pre-commit hook by `@jfrost-mo`_ in :pr:`1154`
* Rename workflow conda lock files by `@jfrost-mo`_ in :pr:`1157`
* Always build conda environment within workflow share directory by `@jfrost-mo`_ in :pr:`1156`
* Break long names in sidebar by `@jfrost-mo`_ in :pr:`1160`
* Allow release workflow to run on pre-releases by `@jfrost-mo`_ in :pr:`1161`
* Unify documentation building Action into pull requests check workflow by `@jfrost-mo`_ in :pr:`1159`
* Small additions to regrid and callback by `@jwarner8`_ in :pr:`1158`
* Fix conda failure by `@jfrost-mo`_ in :pr:`1162`
* Revert to python 3.12 for workflow environment by `@jfrost-mo`_ in :pr:`1168`
* Add missing settings to example suite config by `@jfrost-mo`_ in :pr:`1169`
* Remove any repeated or UM colorbars by `@daflack`_ in :pr:`1177`
* Fix JSON colorbar entries and ensure we use LFRic names by `@jwarner8`_ in :pr:`1178`
* Add colorbar ranges for different pressure levels by `@daflack`_ in :pr:`1181`
* Add shellcheck to pre-commit hooks by `@jfrost-mo`_ in :pr:`1184`
* Set website display date at plot creation by `@jfrost-mo`_ in :pr:`1186`
* Fix timeseries ylim based on JSON entries, and add gridlines by `@jwarner8`_ in :pr:`1175`
* Append suffix to difference cube long name by `@jfrost-mo`_ in :pr:`1189`
* Simplify logging by `@jfrost-mo`_ in :pr:`1185`
* Fix color bars by `@daflack`_ in :pr:`1193`
* Fix colorbar for geopotential height differences by `@daflack`_ in :pr:`1195`
* Add fixes for vertical line xlim and PDF xlim by `@jwarner8`_ in :pr:`1182`
* Test matplotlib font logs are filtered out by `@jfrost-mo`_ in :pr:`1200`
* Remove unneeded callback by `@jwarner8`_ in :pr:`1205`
* Error build_conda when local CSET path not set by `@jfrost-mo`_ in :pr:`1203`
* Draw attention to the hyperlink to download the example by `@jfrost-mo`_ in :pr:`1211`
* Create needed parent directories when writing the website by `@jfrost-mo`_ in :pr:`1219`
* Remove tox by `@jfrost-mo`_ in :pr:`1220`
* Updated vertical line series pressure maximum y limit to 100hPa by `@mo-LewisBlunn`_ in :pr:`1223`
* Modify `ensure_aggregatable_across_cases` to ensure NetCDF cubes are correctly merged by `@jfrost-mo`_ in :pr:`1199`
* Model level callback to allow LFRic cubes to merge by `@daflack`_ in :pr:`1227`
* Sort diagnostics by display name by `@jfrost-mo`_ in :pr:`1229`
* Add iris-grib to dev dependencies by `@jfrost-mo`_ in :pr:`980`
* Add case date as subcategory for output website by `@Sylviabohnenstengel`_ in :pr:`1208`
* Increase memory and wall clock limits for case aggregation tasks by `@daflack`_ in :pr:`1236`

New Contributors

* `@ukmo-huw-lewis`_ made their first contribution in :pr:`898`
* `@mo-sanamahmood`_ made their first contribution in :pr:`934`
* `@cehalliwell`_ made their first contribution in :pr:`943`
* `@BernardClaxton`_ made their first contribution in :pr:`1138`
* `@mo-LewisBlunn`_ made their first contribution in :pr:`1223`

.. _@ukmo-huw-lewis: https://github.com/ukmo-huw-lewis
.. _@mo-sanamahmood: https://github.com/mo-sanamahmood
.. _@BernardClaxton: https://github.com/BernardClaxton
.. _@mo-LewisBlunn: https://github.com/mo-LewisBlunn


24.8.0 (2024-08-29)
-------------------

This release contains a large number of bug fixes and small improvements, and
sets the stage for the major cycling improvement (:issue:`750`) coming in the
next release in a few days.

* Added line wrapping for title by `@Sylviabohnenstengel`_ in :pr:`935`
* Parse recipe variables as python literals by `@jfrost-mo`_ in :pr:`683`
* Fixed metplus config issue  by `@dasha-shchep`_ in :pr:`693`
* Clarify error message on missing files by `@jfrost-mo`_ in :pr:`663`
* Update testing.rst by `@Sylviabohnenstengel`_ in :pr:`696`
* Correct rst syntax added in #696 by `@jfrost-mo`_ in :pr:`700`
* Suggest descriptive PR titles instead of changelog entry by `@jfrost-mo`_ in
  :pr:`701`
* Improve PR title documentation in developer's guide by `@jfrost-mo`_ in
  :pr:`707`
* Remove Fixes placeholder in PR template by `@jfrost-mo`_ in :pr:`705`
* Update section header to match PR checklist item by `@jfrost-mo`_ in :pr:`704`
* Minor wording tweak in marking PR as ready to review docs by `@jfrost-mo`_ in
  :pr:`702`
* Add canonical URL links to documentation by `@jfrost-mo`_ in :pr:`650`
* Clarify running specific tests by `@jfrost-mo`_ in :pr:`703`
* Fix SET_SUBAREA being required to run some LFRIC recipes by `@dasha-shchep`_
  in :pr:`717`
* Remove deprecated postage stamp contour plot operator by `@jfrost-mo`_ in
  :pr:`710`
* Remove unneeded fallback code for old recipe step keys by `@jfrost-mo`_ in
  :pr:`711`
* Test vertical plotting with a filename specified by `@jfrost-mo`_ in :pr:`712`
* Test running recipes with no collate steps and running with a specified style
  file by `@jfrost-mo`_ in :pr:`713`
* Test handling of masked arrays in convection operators, and load convection
  test files with fixtures by `@jfrost-mo`_ in :pr:`714`
* Ignore cartopy DownloadWarning in pytest by `@jfrost-mo`_ in :pr:`716`
* LFRic extension to vertical profile by `@Sylviabohnenstengel`_ in :pr:`638`
* Remove unneeded rose edit setting by `@jfrost-mo`_ in :pr:`722`
* Test higher dimensional orography handling in convection operators by
  `@jfrost-mo`_ in :pr:`715`
* Support STASH codes in generate_var_constraint by `@jfrost-mo`_ in :pr:`723`
* Add cross-section transect functionality by `@jwarner8`_ in :pr:`531`
* Extend UM vertical plotting to model level by `@Sylviabohnenstengel`_ in
  :pr:`697`
* UM spatial plot on model levels by `@Sylviabohnenstengel`_ in :pr:`699`
* Enable spatial fields on full and half levels by `@Sylviabohnenstengel`_ in
  :pr:`695`
* Fix bug in transect operator by `@jwarner8`_ in :pr:`731`
* Unquote double quoted shell values by `@jfrost-mo`_ in :pr:`729`
* Remove invalid rose meta trigger for removed variable by `@jfrost-mo`_ in
  :pr:`733`
* Add _utils operators to internal function documentation by `@jfrost-mo`_ in
  :pr:`735`
* Don't check documentation hyperlinks in commit CI by `@jfrost-mo`_ in
  :pr:`749`
* Generate Histograms for 2D field by `@Sylviabohnenstengel`_ in :pr:`594`
* Tidy up documentation around recipes and cset bake command, introducing
  examples by `@Sylviabohnenstengel`_ in :pr:`641`
* Create operator to combine Cubes/CubeList into single CubeList by `@jwarner8`_
  in :pr:`738`
* Update copyright attribution per legal advice by `@jfrost-mo`_ in :pr:`753`
* Regrid to take CubeList and Cubes by `@jwarner8`_ in :pr:`734`
* Enhance level filter operator to return all vertical levels by `@jwarner8`_ in
  :pr:`728`
* Mass retrieval fix by `@jwarner8`_ in :pr:`759`
* Copy source files from any named folder when installing locally by
  `@jfrost-mo`_ in :pr:`472`
* Add missing brackets to TemporaryDirectory call when installing local CSET by
  `@jfrost-mo`_ in :pr:`760`
* Move all website files under the workflow shared directory by `@jfrost-mo`_ in
  :pr:`764`
* Fix overwriting when using transect on multiple variables by `@jwarner8`_ in
  :pr:`766`
* Add Q-Q plot functionality by `@daflack`_ in :pr:`642`
* Add nc-time-axis to dependencies by `@jwarner8`_ in :pr:`767`
* Fix plot frames jumping around by `@jwarner8`_ in :pr:`772`
* Surface field histogram by `@Sylviabohnenstengel`_ in :pr:`640`
* Preload plot images on web page by `@jfrost-mo`_ in :pr:`781`
* Extract single point data by `@JKPShonk`_ in :pr:`577`
* Filter irrelevant warning raised by regrid test by `@jfrost-mo`_ in :pr:`796`
* Merge and concatenate cubes on load by `@jfrost-mo`_ in :pr:`790`
* Allow Point cell methods for empty constraint, making it possible to unify UM
  and LFRic recipes by `@jfrost-mo`_ in :pr:`778`
* Merge install_local_cset into build_conda so environment is setup in a single
  cylc task by `@jfrost-mo`_ in :pr:`791`
* Convert time AuxCoord to DimCoord for LFRic data by `@jfrost-mo`_ in :pr:`789`
* Cancel running PR checks if new commit is pushed by `@jfrost-mo`_ in :pr:`793`
* Stop ruff warning about ignore-init-module-imports by `@jfrost-mo`_ in
  :pr:`800`
* Parsing of float in workflow by `@jwarner8`_ in :pr:`802`
* Configurable plotting resolution by `@jfrost-mo`_ in :pr:`803`
* General small plot improvements and website organisation by `@jwarner8`_ in
  :pr:`801`
* Set figsize to consistent 8 by 8 inches, and reduce resolution to 100 dpi by
  `@jfrost-mo`_ in :pr:`786`
* Remove LFRic specific recipes now recipes can handle both UM and LFRic data by
  `@jfrost-mo`_ in :pr:`805`
* Move workflow utility code into unstable module within CSET package by
  `@jfrost-mo`_ in :pr:`792`
* Add pcolormesh plotting operator by `@jfrost-mo`_ in :pr:`787`
* Use pcolormesh for Quicklook surface spatial plots by `@jfrost-mo`_ in :pr:`788`
* Create the plot index in finish_website to avoid a data race between
  concurrent index writers by `@jfrost-mo`_ in :pr:`794`
* `@dasha-shchep`_ Fixes METPLUS metadata issue in :pr:`692`
* `@JKPShonk`_ and `@cehalliwell`_ added functionality to CSET to allow it to
   generate time series plots from model data mapped on to a selected
   longitude/latitude location in :pr:`577`
* `@Sylviabohnenstengel`_ add pdf functionality for spatial fields in :pr:`594`.
* `@Sylviabohnenstengel`_ documentation: add info on quick pytesting in
  :pr:`696`
* `@Sylviabohnenstengel`_ add constraint operator for lfric full_levels and
  half_levels
* `@Sylviabohnenstengel`_ introduced lfric_model_level and
  lfric_model_level_field to rose meta
* `@Sylviabohnenstengel`_ expand plot operator add plotting lfric vertical
  profiles on model levels
* `@Sylviabohnenstengel`_ expand plot operator add plotting on model levels to
  spatial plot operator
* `@Sylviabohnenstengel`_ added new recipe for plotting vertical profiles on
  model levels for lfric.
* `@Sylviabohnenstengel`_ added new recipe for plotting spatial lfric data on
  model levels.
* `@Sylviabohnenstengel`_ added a vertical line plotting operator that plots
  vertical profiles using an optional series coordinate and an optional sequence
  coordinate. The series coordinate is currently tested for pressure and the
  sequence coordinate allows displaying vertical profiles over time using the
  time slider functionality. Further added a recipe to plot vertical profiles
  and test functions for the vertical plot operator.Fixes :pr: `494`

24.6.0 (2024-06-17)
-------------------

This release contains a quite a number of small improvements, increasing the
reliability of CSET significantly, and paving the way for further improvements
to come.

* `@jfrost-mo`_ replaced how the encoding of subprocess output is determined in
  :pr:`604`. This adds support for python before 3.11, and more accurately
  reflects the encoding.
* `@jwarner8`_ add intelligent determination of whether to plot country lines in
  :pr:`655`
* `@daflack`_ fixed inflow properties recipe in :pr:`662`
* `@daflack`_ added science review guidance to the documentation in :pr:`649`
* `@jfrost-mo`_ ensured cartopy data files are included in the GitHub Actions
  cache in :pr:`647`
* `@jfrost-mo`_ improved the error message for missing data files in :pr:`663`
* `@jfrost-mo`_ grouped the package install logs in GitHub Actions in :pr:`645`
* `@daflack`_ added an inflow layer properties diagnostic in :pr:`353`
* `@jfrost-mo`_ fixed LFRic cube metadata on load in :pr:`627`. This means that
  loading LFRic data no longer requires special steps in the recipe.
* `@jfrost-mo`_ made the ``install_restricted_files.sh`` script non-interactive
  in :pr:`606`. This should make it less confusing to use.
* `@Sylviabohnenstengel`_ added information to rose-meta for colorbar selection
  and provided path to example JSON file in :pr:`632`
* `@jfrost-mo`_ added a Generative AI policy in :pr:`624`
* `@jfrost-mo`_ linked to the `CSET discussion forum`_ in :pr:`625`
* `@jwarner8`_ use common operator to identify x/y coord names in regrid
  operator :pr:`626`
* `@jwarner8`_ added generic cube util for common functions so all operators can
  use to reduce repetition in :pr:`620`
* `@JorgeBornemann`_ added METPlus GridStat functionality (NIWA) in :pr:`629`
* `@jfrost-mo`_ added a code of conduct in :pr:`618`
* `@jfrost-mo`_ fixed some rose edit metadata so the subarea selectors show up
  when enabled in :pr:`612`
* `@jfrost-mo`_ removed some old recipes that are now redundant in :pr:`512`
* `@jfrost-mo`_ added a git cheat sheet to the documentation in :pr:`598`
* `@jfrost-mo`_ added a warning when input files don't exist in :pr:`518`. This
  makes it easier to see if configuration mistakes were made.
* `@jfrost-mo`_ improved the documentation for adding a new diagnostic in
  :pr:`603`
* `@dasha-shchep`_ added ``generate_area_constraint`` operator and added to
  LFRic recipes in :pr:`522`. This was their first contribution 🎉
* `@Sylviabohnenstengel`_ added a vertical line plotting operator that plots
  vertical profiles using an optional series coordinate and an optional sequence
  coordinate in :pr:`567`. The series coordinate is currently tested for
  pressure and the sequence coordinate allows displaying vertical profiles over
  time using the time slider functionality. Furthermore added a recipe to plot
  vertical profiles and test functions for the vertical plot operator.
* `@jfrost-mo`_ dropped python 3.9 support in :pr:`448` The minimum required
  python is now 3.10.
* `@jfrost-mo`_ fixed some outdated documentation examples in :pr:`546`
* `@jfrost-mo`_ added setuptools as an explicit dependency of the workflow in
  :pr:`543`
* `@cjohnson-pi`_ added support for custom plotting styles in :pr:`570`. This
  avoids many issues of side-by-side plots having different scales, or extreme
  values causing plots to saturate.
* `@Sylviabohnenstengel`_ documentation: removed necessity to add new recipe to flow.cylc.
* `@Ashfinn`_ fixed a typo in the documentation in :pr:`573`. This was their
  first contribution 🎉
* `@jfrost-mo`_ fixed how arguments from the ``CSET_ADDOPTS`` environment
  variable are parsed in :pr:`569`. This fixes issues with passing lists into
  recipes.
* `@jfrost-mo`_ added a dead link checker to the documentation in :pr:`556`
* `@Sylviabohnenstengel`_ documented the common error of operating on a CubeList
  instead of a Cube in :pr:`541`
* `@Sylviabohnenstengel`_ documented how to update your conda environment in
  :pr:`519`
* `@Sylviabohnenstengel`_ documented the common error of no cubes being loaded
  in :pr:`513`
* `@Sylviabohnenstengel`_ and `@jfrost-mo`_ redid the rose-meta sort orders so
  that workflow configuration makes more sense in :pr:`504`
* `@jfrost-mo`_ updated the example rose-suite.conf to reflect what a modern
  version should look like in :pr:`508`

.. _@JKPShonk: https://github.com/JKPShonk
.. _@cehalliwell: https://github.com/cehalliwell

.. _CSET discussion forum: https://github.com/MetOffice/simulation-systems/discussions/categories/cset-toolkit
.. _@dasha-shchep: https://github.com/dasha-shchep
.. _@cjohnson-pi: https://github.com/cjohnson-pi
.. _@Ashfinn: https://github.com/Ashfinn

24.4.1 (2024-04-19)
-------------------

This release contains a large generalisation of the CSET workflow, allowing use
of templating to use the same recipe for multiple variables. It also adds
cycling to the workflow, so a long workflow can be efficiently processed in
parallel.

* `@jfrost-mo`_ added GitHub Issue and Pull Request templates, and a detailed
  contribution checklist to the documentation in :pr:`465`
* `@jfrost-mo`_ added a changelog in :pr:`468`
* `@jfrost-mo`_ documented the ``category`` recipe key in :pr:`499`
* `@jfrost-mo`_ renamed the ``steps`` and ``post-steps`` keys to ``parallel``
  and ``collate`` in :pr:`484`. This makes them more meaningful, but is a
  **breaking change**.
* `@daflack`_ added some generic arithmetic operators in :pr:`452`
* `@jfrost-mo`_ made the log output of the read operator nicer in :pr:`461`
* `@jfrost-mo`_ added links to share feedback to the output page in :pr:`442`
* `@jfrost-mo`_ documented some common errors in :pr:`443`
* `@jfrost-mo`_ documented the deprecation policy in :pr:`444`
* `@jfrost-mo`_ fixed an iris deprecation warning for save_split_attrs in :pr:`459`
* `@jfrost-mo`_ added LFRic specific recipes in :pr:`462`. This allows CSET to
  read in structured LFRic data.
* `@jfrost-mo`_ fixed a memory leak when plotting in :pr:`482`
* `@jfrost-mo`_ included the recipe title in the plot title, giving more context
  to the output. This was :pr:`462`
* `@Sylviabohnenstengel`_ added the capability to loop over model levels in :pr:`441`
* `@Sylviabohnenstengel`_ and `@jfrost-mo`_ renamed and better linked up the
  :doc:`/contributing/index` in :pr:`434` and :pr:`435`
* `@jfrost-mo`_ updated the documentation Actions workflow to make it simpler and
  faster in :pr:`449`
* `@jfrost-mo`_ added a cycling to the cylc workflow so recipes can be run in
  parallel across multiple nodes. This was :pr:`395`
* `@jfrost-mo`_ added looping inside an include file for generalisation in :pr:`387`
* `@jwarner8`_ added a basic regridding operator in :pr:`405`
* `@jfrost-mo`_ made conda-lock update PRs use a GitHub App in :pr:`415`
* `@Sylviabohnenstengel`_ retitled code and tooling setup page in :pr:`433`
* `@Sylviabohnenstengel`_ updated git terminology in :pr:`436`
* `@jfrost-mo`_ added sequential plot display with unified postage stamp plots in :pr:`379`
* `@JorgeBornemann`_ fixed IFS in build conda in :pr:`447`
* `@jfrost-mo`_ added a licence header to convection tests in :pr:`450`

.. _@JorgeBornemann: https://github.com/JorgeBornemann
.. _@jwarner8: https://github.com/jwarner8

24.2.1 (2024-03-04)
-------------------

A small bug fix release containing several fixes that ensure portability on
Australia's NCI system.

* Graceful error when graphing without xdg-open by `@jfrost-mo`_ in :pr:`394`
* Docs update by `@jfrost-mo`_ in :pr:`392`
* Update workflow conda lockfiles automatically by `@jfrost-mo`_ in :pr:`410`
* Handle ``LD_LIBRARY_PATH`` being unset by `@jfrost-mo`_ in :pr:`404`

24.2.0 (2024-02-13)
-------------------

This release open sources the cylc workflow, allowing for much easier running of
CSET over large datasets. It also includes support for parametrising recipes to
allow a single recipe to work for many cases.

* Open source workflow by `@jfrost-mo`_ in :pr:`247`
* CAPE ratio diagnostic by `@daflack`_ in :pr:`325`
* CAPE ratio rose edit tweak by `@daflack`_ in :pr:`332`
* Minor bug fix to cape ratio documentation by `@daflack`_ in :pr:`336`
* Use cached conda environment for CI by `@jfrost-mo`_ in :pr:`351`
* Single cube read operator by `@jfrost-mo`_ in :pr:`323`
* Hash updated config ensuring unique branch by `@jfrost-mo`_ in :pr:`350`
* Add filter_multiple_cubes operator by `@jfrost-mo`_ in :pr:`362`
* Test exception for invalid output directory by `@jfrost-mo`_ in :pr:`364`
* Test no constraints given to filter_multiple_cubes by `@jfrost-mo`_ in :pr:`363`
* Update workflow-installation.rst by `@Sylviabohnenstengel`_ in :pr:`365`
* Recipe parametrisation by `@jfrost-mo`_ in :pr:`337`
* Fix crash when running recipe from env var by `@jfrost-mo`_ in :pr:`384`

0.5.0 (2023-11-24)
------------------

Small update featuring some better looking plots (though still a
work-in-progress, see :issue:`240`) and a documentation fix.

* Bump version to 0.5.0 by `@jfrost-mo`_ in :pr:`278`
* Improve contour plot by `@jfrost-mo`_ in :pr:`282`

0.4.0 (2023-11-23)
------------------

Containing many months of work, this release contains many usability
improvements, new generic operators, and a big change to the output, where it is
now generated as handily viewable HTML pages.

* Update version to 0.4.0 by `@jfrost-mo`_ in :pr:`180`
* Postage stamp plots by `@jfrost-mo`_ in :pr:`160`
* Add collapse operator with corresponding yaml file and changes  by `@Sylviabohnenstengel`_ in :pr:`168`
* Make plot.contour_plot and write.write_cube_to_nc return a cube by `@jfrost-mo`_ in :pr:`183`
* Postage stamp plot fix by `@jfrost-mo`_ in :pr:`181`
* Document collapse operator by `@jfrost-mo`_ in :pr:`185`
* Refactor tests to use PyTest helpers by `@jfrost-mo`_ in :pr:`177`
* Document installing CSET into its own environment by `@jfrost-mo`_ in :pr:`198`
* Update README.md by `@Sylviabohnenstengel`_ in :pr:`206`
* Use hash of updated lock files in branch name by `@jfrost-mo`_ in :pr:`201`
* Add note on updating a cloned repository by `@jfrost-mo`_ in :pr:`190`
* Skip build-docs on push to main by `@jfrost-mo`_ in :pr:`200`
* Python 3.12 support by `@jfrost-mo`_ in :pr:`202`
* Update README.md by `@Sylviabohnenstengel`_ in :pr:`225`
* Update README.md by `@Sylviabohnenstengel`_ in :pr:`226`
* Update why-cset.rst by `@Sylviabohnenstengel`_ in :pr:`227`
* Fix globbing for lock file hashing by `@jfrost-mo`_ in :pr:`229`
* Update index.rst by `@Sylviabohnenstengel`_ in :pr:`228`
* Update index.rst by `@Sylviabohnenstengel`_ in :pr:`230`
* Use static branch name while updating lock files by `@jfrost-mo`_ in :pr:`245`
* Swap out flake8 for Ruff by `@jfrost-mo`_ in :pr:`218`
* Including aggregate operator by `@Sylviabohnenstengel`_ in :pr:`241`
* Fix filter operator for filtering cube by `@daflack`_ in :pr:`258`
* Fix pre-commit mangling test data by `@jfrost-mo`_ in :pr:`273`
* Improve tutorials by `@jfrost-mo`_ in :pr:`209`
* Model level constraint operator by `@Sylviabohnenstengel`_ in :pr:`272`
* Plot generation improvements by `@jfrost-mo`_ in :pr:`274`

.. _@daflack: https://github.com/daflack

0.3.0 (2023-08-02)
------------------

This release contains some major changes to the user experience. This includes
many of the CLI commands changing names, and the :doc:`/index` being completely
restructured. Hopefully this should be the last major reshuffle of the user
experience, as we are getting closers to being feature complete for our MVP.

Other highlights include the addition of the :ref:`cset-graph-command` command
for visualising recipes, and the :ref:`cset-cookbook-command` command for
dumping the built in recipes to disk.

* Operator runner improvements by `@jfrost-mo`_ in :pr:`128`
* Add codespell pre-commit hook by `@jfrost-mo`_ in :pr:`135`
* Add graph command to visualise recipe files by `@jfrost-mo`_ in :pr:`136`
* Pin version of tox used in environment by `@jfrost-mo`_ in :pr:`142`
* Increase version number by `@jfrost-mo`_ in :pr:`124`
* Update description of CSET by `@jfrost-mo`_ in :pr:`141`
* Refactoring by `@jfrost-mo`_ in :pr:`144`
* Rename run command to bake by `@jfrost-mo`_ in :pr:`143`
* Add command to create recipes on disk by `@jfrost-mo`_ in :pr:`140`
* Documentation restructure by `@jfrost-mo`_ in :pr:`151`
* Add version command by `@jfrost-mo`_ in :pr:`156`
* General cleanup by `@jfrost-mo`_ in :pr:`158`
* Remove Python 3.8 support by `@jfrost-mo`_ in :pr:`173`
* Fix install instructions in docs by `@jfrost-mo`_ in :pr:`176`
* Allow PR checks to be run manually by `@jfrost-mo`_ in :pr:`179`
* Ensemble ingestion with read operator by `@jfrost-mo`_ in :pr:`157`
* Update working practices link to point to contributing docs by `@jfrost-mo`_ in :pr:`175`

0.2.0 (2023-06-16)
------------------

Lots of good work in the release towards making the recipe format more usable.

* Update installation instructions to use conda and add missing operators to documentation by `@jfrost-mo`_ in :pr:`94`
* Update index.rst by `@Sylviabohnenstengel`_ in :pr:`95`
* Improve installation instructions by `@jfrost-mo`_ in :pr:`97`
* Use speedy libmamba when resolving conda environments by `@jfrost-mo`_ in :pr:`105`
* Add documentation on rational by `@jfrost-mo`_ in :pr:`102`
* Relax version requirement for sphinx by `@jfrost-mo`_ in :pr:`108`
* Run PR checks on push to main by `@jfrost-mo`_ in :pr:`109`
* Move to YAML recipe format by `@jfrost-mo`_ in :pr:`119`
* Lock pre-commit config to specific SHA by `@jfrost-mo`_ in :pr:`118`
* Use recipes from environment variable by `@jfrost-mo`_ in :pr:`122`

.. _@Sylviabohnenstengel: https://github.com/Sylviabohnenstengel

0.1.0 (2023-04-24)
------------------

The first release of CSET! 🎉 This release contains basic operators to do
reading, writing, filtering, and plotting of data. It is however still quite
limited in each of them, and still doesn't promise much in the way of API
stability, with things undoubtedly going to undergo significant change in the
near future.

This release also serves as a basis for packaging CSET out into the wider world;
packages will be released on `PyPI <https://pypi.org/project/CSET/>`_, and
`conda-forge <https://anaconda.org/conda-forge/cset>`_.

* Re-enable testing on python 3.11 by `@jfrost-mo`_ in :pr:`61`
* Operator runner improvements by `@jfrost-mo`_ in :pr:`56`
* Move METplus tasks out of command line repository by `@jfrost-mo`_ in :pr:`76`
* Remove extra punctuation from conda lock CI commit message by `@jfrost-mo`_ in :pr:`78`
* Measure test coverage by `@jfrost-mo`_ in :pr:`68`
* Improve test coverage by `@jfrost-mo`_ in :pr:`81`
* Fix link to Git tutorial by `@jfrost-mo`_ in :pr:`83`
* Fix description of a git tag by `@jfrost-mo`_ in :pr:`84`
* Add basic plotting capabilities by `@jfrost-mo`_ in :pr:`85`
* Make PR coverage reports edit last comment by `@jfrost-mo`_ in :pr:`92`
* Package on PyPI by `@jfrost-mo`_ in :pr:`90`

.. _@jfrost-mo: https://github.com/jfrost-mo
