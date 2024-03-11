#! /usr/bin/env python3

"""Development module for getting the correct file for a validity time."""

import logging
import re
from datetime import datetime, timedelta

import isodate


def word_month_to_num(month: str) -> int:
    """Convert a string month into the corresponding number.

    E.g. "January" -> 1, "feb" -> 2.

    Returns
    -------
    KeyError:
        If month is not a valid month name.
    """
    month_mappings = {
        "jan": 1,
        "feb": 2,
        "mar": 3,
        "apr": 4,
        "may": 5,
        "jun": 6,
        "jul": 7,
        "aug": 8,
        "sep": 9,
        "oct": 10,
        "nov": 11,
        "doc": 12,
    }
    # Leave exceptions to caller.
    month_number = month_mappings[month.lower()[:3]]
    return month_number


def validity_time_direct(times: dict) -> datetime:
    """Extract the validity time directly."""
    try:
        month = times["valid_month"]
    except KeyError:
        month = word_month_to_num(times["valid_word_month"])
    validity_time = datetime(
        int(times["valid_year"]),
        int(month),
        int(times["valid_day"]),
        int(times.get("valid_minute", 0)),
        int(times.get("valid_hour", 0)),
    )
    return validity_time


def validity_time_from_init_time(times: dict) -> datetime:
    """Derive the validity time from the initiation time and lead time."""
    try:
        month = times["init_month"]
    except KeyError:
        month = word_month_to_num(times["init_word_month"])
    initiation_time = datetime(
        int(times["init_year"]),
        int(month),
        int(times["init_day"]),
        int(times.get("init_hour", 0)),
        int(times.get("init_minute", 0)),
    )
    lead_time = timedelta(hours=int(times["lead_hour"]))
    validity_time = initiation_time + lead_time
    return validity_time


def all_validity_info(pattern: str) -> bool:
    """Check the validity time is present."""
    return (
        "{valid_year}" in pattern
        and ("{valid_month}" in pattern or "{valid_word_month}" in pattern)
        and "valid_day" in pattern
    )


def all_init_info(pattern: str) -> bool:
    """Check the initiation time and lead time are present."""
    return (
        "{init_year}" in pattern
        and ("{init_month}" in pattern or "{init_word_month}" in pattern)
        and "{init_day}" in pattern
        and "{lead_hour}" in pattern
    )


def create_validity_time_tester(
    pattern: str,
    validity_time: str,
    period_length: str,
    times_per_file: int,
    time_offset: int,
) -> callable:
    """Get a function to test if a filename contains a certain validity time.

    Parameters
    ----------
    pattern: str
        The pattern of the filename, with time information marked.
    validity_time: str
        ISO 8601 datetime string of the desired validity time. Any timezone
        information are removed, and it is used as a naive datetime.
    period_length: str
        The length of time between time values in the file as an ISO 8601
        duration.
    times_per_file: int
        The number of validity times per file. A positive number indicates the
        data is after the indicated time, and a negative number indicates the
        data is before.
    time_offset: int
        Indicates the offset in time periods between the marked validity time
        and the earliest time in the file. E.g. if the filename was T06, then +2
        would mean the first contained time was T04, while -2 would mean the
        first time was T08.

    Returns
    -------
    test_function: callable
        A function that tests a filename and returns True when the validity time
        is contained, and False when not.

    Notes
    -----
    The pattern format is the filename with a number of placeholders added to
    mark where the time information is. You must have enough information to
    get the validity time, either directly from the validity time, or derived
    from the initiation time and lead time.

    Validity time placeholders:
    * ``{valid_year}``
    * ``{valid_month}``
    * ``{valid_word_month}``
    * ``{valid_day}``
    * ``{valid_hour}``
    * ``{valid_minute}``

    Initiation time placeholders:
    * ``{init_year}``
    * ``{init_month}`` Numeric month, e.g: 02
    * ``{init_word_month}`` Wordy month, e.g: feb
    * ``{init_day}``
    * ``{init_hour}``
    * ``{init_minute}``
    * ``{lead_hour}``
    """
    # Check that the pattern has sufficient information.
    logging.debug("Original pattern: %s", pattern)
    if all_validity_info(pattern):
        logging.info("Taking validity time directly from filename.")
        calc_validity_time = validity_time_direct
    elif all_init_info(pattern):
        logging.info("Deriving validity time from initialisation time and lead time.")
        calc_validity_time = validity_time_from_init_time
    else:
        raise ValueError(
            "Not enough information to determine validity time in pattern."
        )

    # Construct a regex for capturing the desired information.
    replacements = {
        # "old": "new",
        "{init_year}": r"(?P<init_year>[0-9]{4})",
        "{init_month}": r"(?P<init_month>[0-9]{2})",
        "{init_word_month}": r"(?P<init_word_month>[a-zA-Z]{3,9})",
        "{init_day}": r"(?P<init_day>[0-9]{2})",
        "{init_hour}": r"(?P<init_hour>[0-9]{2})",
        "{init_minute}": r"(?P<init_minute>[0-9]{2})",
        "{valid_year}": r"(?P<valid_year>[0-9]{4})",
        "{valid_month}": r"(?P<valid_month>[0-9]{2})",
        "{valid_word_month}": r"(?P<valid_word_month>[a-zA-Z]{3,9})",
        "{valid_day}": r"(?P<valid_day>[0-9]{2})",
        "{valid_hour}": r"(?P<valid_hour>[0-9]{2})",
        "{valid_minute}": r"(?P<valid_minute>[0-9]{2})",
        "{lead_hour}": r"(?P<lead_hour>[0-9]{2,3})",
    }
    for key in replacements:
        pattern = pattern.replace(key, replacements[key])
    logging.info("Regex: %s", pattern)

    # After converting to datetime remove the timezone so we can just compare
    # naive dates for ease. Only one timezone should be used in a set of files.
    target_validity_time = datetime.fromisoformat(validity_time).replace(tzinfo=None)
    period_duration = isodate.parse_duration(period_length)
    start_offset = time_offset * period_duration
    end_offset = times_per_file * period_duration

    def test_function(filename: str) -> bool:
        """Whether the filename contains the validity time."""
        match = re.match(pattern, filename)
        if match is None:
            return False
        times = match.groupdict()
        logging.debug(times)
        file_time_start = calc_validity_time(times) - start_offset
        file_time_end = file_time_start + end_offset
        return (
            file_time_start <= target_validity_time
            and target_validity_time < file_time_end
        )

    return test_function
