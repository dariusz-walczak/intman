"""Capacity data processing helpers"""

# Standard library imports
import datetime

# Third party imports
import dateutil.parser
import numpy


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
        "workday count": workday_count,
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
