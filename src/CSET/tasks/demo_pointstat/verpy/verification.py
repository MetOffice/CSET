"""
Contains functions for use with VerPy plotting scripts.
"""
import copy
import numpy
import config
from VerPy.case import Case
from VerPy.data import Data
from VerPy.options import Options
from VerPy.parameter import ParameterDict


def comps_to_data(summary_data, case_num):
    """
    Convert component cases from each subjob into a single case.
    The first case is used to set up the dimensions.
    """

    params = [
        ParameterDict(name=k, unit=None, set_other=False) for k in summary_data.keys()
    ]
    base_key = summary_data.keys()[0]
    base = summary_data[base_key][0]
    for s in base.stats:
        s["agg"] = numpy.mean  # Do a simple mean
    if "scales" in base.dims:
        dat = Data(
            nan_vals=True,
            params=params,
            scales=base.scales,
            stats=base.stats,
            fcrs=base.fcrs,
            dates=base.dates,
        )
    else:
        dat = Data(
            nan_vals=True,
            params=params,
            scales=base.scales,
            stats=base.stats,
            fcrs=base.fcrs,
            dates=base.dates,
        )
    for k, v in summary_data.items():
        dat_ = v[case_num]
        param = ParameterDict(name=k, unit=None, set_other=False)
        for fcr in base.fcrs:
            if "scales" in base.dims:
                for scale in base.scales:
                    new_ind = dat.index({"params": param, "fcrs": fcr, "scales": scale})
                    old_ind = dat_.index({"fcrs": fcr, "scales": scale})
                    if old_ind is not None:
                        dat.vals[new_ind] = numpy.squeeze(dat_.vals[old_ind])
            else:
                new_ind = dat.index({"params": param, "fcrs": fcr})
                old_ind = dat_.index({"fcrs": fcr})
                if old_ind is not None:
                    dat.vals[new_ind] = numpy.squeeze(dat_.vals[old_ind])

    return dat


def get_hira_data(expid, source, comp, n_ens, vts, fcrs):
    """
    Extracts HiRA data from the Area Results Databases, given the source
    files and components passed in, looping over the required
    neighbourhood scales. A 'component' is an options dictionary
    (to be passed to :func:`VerPy.job.run`).

    Assumes the number of bins is 10 for a deterministic model, otherwise the
    number of bins is set to (1 + number_of_ensemble_members).

    :param expid: String containing the experiment id used in the ARD files.
    :param source: String containing the location of the ARD files.
    :param comp: A dictionary containing common options between
                 components
    :returns VerPy.data.Data: A VerPy.data.Data object.
    """
    if n_ens == 1:
        n_bins = 10
    else:
        n_bins = 1 + n_ens

    for i, scale in enumerate(config.HIRA_SCALES):
        opts = {
            "jobid": "HiRAExtract",
            "expids": "{}{:02}".format(expid, scale),
            "source": source,
            "times": vts,
            "fcrs": fcrs,
        }

        opts.update(comp)
        # Set ensopts for CRPS according to scale
        if comp["stat"] == 40813:
            opts["ensopts"] = 1 + n_ens * scale**2
        else:
            opts["ensopts"] = n_bins
            opts["probbins"] = [(x + 0.5) / n_bins for x in range(0, n_bins)]
        opts = Options(opts)
        case = Case(opts)
        case.load_data()

        case.data.expand_dims("scales", scale)
        if hasattr(case.data, "_base_data"):
            del case.data._base_data
        if i == 0:
            dat = copy.deepcopy(case.data)
        else:
            dat.concatenate(case.data)

    return dat


def get_pers_data(expid, source, comp, n_ens, vts):
    """
    Gets the relevant persistence data out of the Area Results Database file.

    Assumes the number of bins is 10 for a deterministic model, otherwise the
    number of bins is set to (1 + number_of_ensemble_members).

    :param expid: String containing the experiment id used in the ARD files.
    :param source: String containing the location of the ARD files.
    :param comp: A dictionary containing common options between
                 components
    :returns VerPy.data.Data: A VerPy.data.Data object.
    """

    if n_ens == 1:
        n_bins = 10
    else:
        n_bins = 1 + n_ens

    scale = config.HIRA_SCALES[0]

    opts = {
        "jobid": "HiRAExtractPers",
        "expids": "{}{:02}_P".format(expid, scale),
        "source": source,
        "times": vts,
        "fcrs": 0,
    }

    opts.update(comp)
    # Set ensopts for CRPS according to scale
    if comp["stat"] == 40813:
        opts["ensopts"] = 2
    else:
        opts["ensopts"] = n_bins
        opts["probbins"] = [(x + 0.5) / n_bins for x in range(0, n_bins)]
    opts = Options(opts)
    case = Case(opts)
    case.load_data()

    case.data.expand_dims("scales", scale)
    if hasattr(case.data, "_base_data"):
        del case.data._base_data

    return case.data


def get_hira_components(base_options, use_srews=True):
    """
    Generates a list of hira components based on the options provided.
    A 'component' is an options dictionary (to be passed to :func:`VerPy.job.run`).

    A user-provided dictionary should provide the following keys:

        * start
        * end

    Any other keys (e.g. verbosity) will also be used, but these 7 must
    exist.

    :param base_options: A dictionary containing common options between
                         components
    :return list: A list of component tuples
    """

    # Validate user-options
    if not isinstance(base_options, dict):
        raise Exception(
            "Expecting dictionary argument, got {}.".format(type(base_options))
        )
    for key in ("start", "end"):
        if key not in base_options:
            raise Exception('Expecting key "{}".'.format(key))

    components = [
        {
            "param": (16, 1, -1.0),
            "thresh": [0],
            "stat": 40813,
            "type": "categorical",
            "jobid": "TempCRPS",
            "truth": 10000,
        },
    ]

    # Add common options
    for comp in components:
        comp.update(base_options)

    return components


def get_hira_bias_components(base_options, use_srews=True):
    """
    Generates a list of bias components based on the options provided.
    A 'component' is an options dictionary (to be passed to :func:`VerPy.job.run`).

    A user-provided dictionary should provide the following keys:

        * start
        * end

    Any other keys (e.g. verbosity) will also be used, but these 7 must
    exist.

    :param base_options: A dictionary containing common options between
                         components
    :return list: A list of component tuples
    """

    # Validate user-options
    if not isinstance(base_options, dict):
        raise Exception(
            "Expecting dictionary argument, got {}.".format(type(base_options))
        )
    for key in ("start", "end"):
        if key not in base_options:
            raise Exception('Expecting key "{}".'.format(key))

    components = [
        {
            "param": (16, 1, -1.0),
            "stat": 7051,
            "type": "continuous",
            "jobid": "Temp",
            "truth": 10000,
        },
    ]

    # Add common options
    for comp in components:
        comp.update(base_options)

    return components


def convert_stats(stats):
    """
    If skill scores are required, convert the input statistic object from
    an error score.
    """
    new_stats = []
    for s in stats:
        new = copy.copy(s)
        new["orientation"] = "positive"
        new["range"] = (float("-inf"), 1)
        new["name"] = s["name"].replace("Score", "Skill Score")
        new_stats.append(new)

    return new_stats


def replicate(dat, fcrs):
    """
    Replicates the T+0 persistence data for all forecast lead times
    in the main data object.
    """
    new = copy.copy(dat.vals)
    axis = dat.get_val_axis("fcrs")
    dat.fcrs[0] = fcrs[0]
    for i, fcr in enumerate(fcrs[1:]):
        dat.vals = numpy.concatenate((dat.vals, new), axis=axis)
        dat.fcrs.append(fcr)


def get_profile_components(base_options, levels):
    """
    Generates a list of profile components based on the options provided.
    A 'component' is an options dictionary (to be passed to :func:`VerPy.job.run`).

    A user-provided dictionary should provide the following keys:

        * start
        * end
        * expids
        * source
        * fcrs

    Any other keys (e.g. verbosity) will also be used, but these 5 must
    exist.

    :param base_options: A dictionary containing common options between
                         components
    :return list: A list of component tuples
    """

    # Validate user-options
    if not isinstance(base_options, dict):
        raise Exception(
            "Expecting dictionary argument, got {}.".format(type(base_options))
        )
    for key in ("start", "end", "expids", "source", "fcrs"):
        if key not in base_options:
            raise Exception('Expecting key "{}".'.format(key))

    components = [
        # Temperature
        {
            "stat": [7051, 7752],
            "type": "continuous",
            "truth": 50000,
            "param": (16, 8, levels),
            "jobid": "Temp",
        },
    ]

    # Add common options
    for comp in components:
        comp.update(base_options)

    return components


def get_surf_components(base_options):
    """
    Generates a list of components based on the options provided.
    A 'component' is an options dictionary (to be passed to :func:`VerPy.job.run`).

    A user-provided dictionary should provide the following keys:

        * start
        * end
        * expids
        * source

    Any other keys (e.g. verbosity) will also be used, but these 4 must
    exist.

    :param base_options: A dictionary containing common options between
                         components
    :return list: A list of component tuples
    """
    # Validate user-options
    if not isinstance(base_options, dict):
        raise Exception(
            "Expecting dictionary argument, got {}.".format(type(base_options))
        )
    for key in ("start", "end", "expids", "source"):
        if key not in base_options:
            raise Exception('Expecting key "{}".'.format(key))

    components = [
        # Temperature
        {
            "stat": [2, 7051, 7752, 7053],
            "type": "cnt",
            "truth": 10000,
            "param": (16, 1, -1.0),
            "jobid": "Temp",
        },
    ]

    # Add common options
    for comp in components:
        comp.update(base_options)

    return components
