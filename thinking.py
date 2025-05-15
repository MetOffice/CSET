#! /usr/bin/env python3

"""Example for a DataGetter class."""

from datetime import datetime, timedelta

from iris.cube import CubeList


class Phenomenon:
    # This is probably the hardest bit of this. The idea is that you would
    # create an instance of this class with a variable name, such as
    # "temperature_at_screen_level", which would represent the concept of that
    # variable. Then when it comes time to filter some data you could use this
    # object in place of a specific variable name and it would filter with the
    # model appropriate variable. That could be achieved either by identifying
    # the model we have (how?) and using the appropriate lingo, or just by
    # trying a few in sequence (do the same names refer to different things in
    # different models?) and taking the first match.
    standard_name: str
    long_names: list[str]
    stash_code: str


class TimeRange:
    time_start: datetime
    time_end: datetime
    # Do we need frequency? Such as grabbing data every hour, day, or month.
    frequency: timedelta


class LatLonPoint:
    # Class with additional logic to constraint coordinates to within range, and
    # implement coordinate addition/wrapping/comparison operations.
    latitude: float
    longitude: float


class RectangularBoundedRegion:
    # A rectangular region should be enough for data selection, though we might
    # need to return slightly more in the case of non-lat-lon data, such as
    # healpix or LFRic.
    p1: LatLonPoint
    p2: LatLonPoint


# class Aggregation:
#     # Do we want this? This might not be standard enough to implement reliably
#     # across sources. I don't think it justifies the complexity at this stage,
#     # and Dasha agrees.
#     pass


class DataGetter:
    """Class for an object that gets data from a source."""

    source: str

    def __init__(self, source: str):
        self.source = source

    def get_cubes(
        self,
        phenomena: list[Phenomenon] | None,
        time: TimeRange | None,
        area: RectangularBoundedRegion | None,
    ) -> CubeList:
        """Get cubes from the source."""
        raise NotImplementedError("This class needs to be subclassed.")


print(DataGetter)

# How much of this is implemented in https://intake.readthedocs.io ?

# So intake does seem pretty useful, and broadly provides a way to go from a URL
# of various kinds to a python object, going through various paths. It does
# provide data subsetting capability, but notably that capability is different
# for different loaders.
#
# Questions:
# 1. How easy is writing a new reader? This doesn't look too bad, and wouldn't
#    be anymore work than writing our own loading code.
# 2. How easy is writing a catalogue?
# 3. How willing am I to accept it as a dependency? While there are a few people
#    in the organisation, there is only one consistent maintainer over the past
#    two years. On the other hand it isn't a huge package outside of the various
#    drivers.
#
# I think my take away is we should probably wrap intake behind our own
# interface, but largely take advantage of it, including writing readers to
# produce iris cubes.
#
# I still need to look into question 2.
