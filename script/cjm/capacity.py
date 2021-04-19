# Copyright © 2020-2021 Mobica Limited. All rights reserved.

"""Capacity data processing helpers"""

# Standard library imports
import datetime
import decimal

# Third party imports
import dateutil.parser
import numpy

# Project imports
import cjm.presentation


def deserialize_dates(iso_dates, start_date, end_date):
    """Deserialize a list of dates and return only these of them which match given time range"""

    def __date_in_sprint(date):
        return start_date <= date < end_date + datetime.timedelta(days=1)

    return sorted(set([
        d for d in [dateutil.parser.parse(s).date() for s in iso_dates]
        if __date_in_sprint(d)]))


def process_team_capacity(sprint_data, capacity_data):
    """Determine actual team capacity basing on the capacity data

    The output of this function shouldn't be dumped directly into json because of
    the not serialized dates in it. If there is a need to dump it into json, some
    additional serialize_team_capacity function should be added.
    """
    sprint_start_date = dateutil.parser.parse(sprint_data["start date"]).date()
    sprint_end_date = dateutil.parser.parse(sprint_data["end date"]).date()
    workday_count = numpy.busday_count(sprint_start_date, sprint_end_date).item()

    national_holidays = deserialize_dates(
        capacity_data["national holidays"], sprint_start_date, sprint_end_date)
    extra_holidays = deserialize_dates(
        capacity_data["additional holidays"], sprint_start_date, sprint_end_date)
    shared_holidays = sorted(national_holidays + extra_holidays)

    return {
        "sprint start date": sprint_start_date,
        "sprint end date": sprint_end_date,
        "workday count": workday_count, # Number or workdays in the sprint BEFORE the shared
                                        #  holidays deduction
        "national holidays": national_holidays,
        "extra holidays": extra_holidays,
        "shared holidays": shared_holidays
    }


def process_person_capacity(team_capacity, person_data):
    """Determine actual personal capacity basing on the team capacity and personal capacity data"""

    shared_count = len(team_capacity["shared holidays"])
    personal_holidays = deserialize_dates(
        person_data["personal holidays"], team_capacity["sprint start date"],
        team_capacity["sprint end date"])
    personal_count = len(personal_holidays)
    daily_capacity = person_data["daily capacity"]
    sprint_workdays = team_capacity["workday count"] - shared_count - personal_count
    sprint_capacity = sprint_workdays * daily_capacity

    return {
        "account id": person_data["account id"],
        "last name": person_data["last name"],
        "first name": person_data["first name"],
        "daily capacity": person_data["daily capacity"],
        "personal holidays": personal_holidays,
        "holidays": sorted(team_capacity["shared holidays"] + personal_holidays),
        "sprint workday count": sprint_workdays,
        "sprint capacity": sprint_capacity
    }


def process_person_capacity_list(sprint_data, capacity_data):
    """Convenience method returning a list of personal capacity data based on provided sprint and
    capacity data"""
    team_capacity = process_team_capacity(sprint_data, capacity_data)
    return [process_person_capacity(team_capacity, p) for p in capacity_data["people"]]


def make_person_capacity_lut(person_capacity_list):
    """Convenience method converting the list returned by process_person_capacity_list to a lookup
    table.

    The method filter outs people without jira account specified"""
    return {p["account id"]: p for p in person_capacity_list if p["account id"]}

def determine_alien_status(commitment_value):
    """Determine commitment ratio status code for given commitment value with the assumption that
    related capacity is zero"""
    if commitment_value > 20:
        return cjm.presentation.STATUS_CODES.HIGHEST
    elif commitment_value > 10:
        return cjm.presentation.STATUS_CODES.HIGHER
    elif commitment_value > 0:
        return cjm.presentation.STATUS_CODES.HIGH
    return cjm.presentation.STATUS_CODES.NEUTRAL


def determine_ratio_status(ratio):
    """Determine commitment ratio status code for given commitment ratio"""
    # pylint: disable=too-many-return-statements
    if ratio < 40:
        return cjm.presentation.STATUS_CODES.LOWEST
    elif ratio < 60:
        return cjm.presentation.STATUS_CODES.LOWER
    elif ratio < 80:
        return cjm.presentation.STATUS_CODES.LOW
    elif ratio > 140:
        return cjm.presentation.STATUS_CODES.HIGHEST
    elif ratio > 120:
        return cjm.presentation.STATUS_CODES.HIGHER
    elif ratio > 100:
        return cjm.presentation.STATUS_CODES.HIGH
    return cjm.presentation.STATUS_CODES.NEUTRAL


def determine_summary(commitment_value, capacity_value):
    """Determine capacity summary for given commitment and capacity values"""
    if capacity_value > 0:
        ratio = (
            decimal.Decimal("{0:d}.0000".format(commitment_value)) /
            decimal.Decimal(capacity_value) * 100)
        ratio = ratio.quantize(decimal.Decimal("0.00"), decimal.ROUND_HALF_UP)
        status = determine_ratio_status(ratio)
    else:
        ratio = None
        status = determine_alien_status(commitment_value - capacity_value)

    return {
        "capacity": capacity_value,
        "commitment": commitment_value,
        "commitment ratio": ratio,
        "commitment status": status
    }
