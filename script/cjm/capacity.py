# Standard library imports
import datetime
import json

# Third party imports
import dateutil.parser
import jsonschema
import numpy

# Project imports
import cjm.schema


def load_data(cfg, capacity_file):
    schema = cjm.schema.load(cfg, "capacity.json")
    data = json.load(capacity_file)
    jsonschema.validate(data, schema)
    return data


def deserialize_dates(iso_dates, start_date, end_date):
    def __date_in_sprint(date):
        return start_date <= date < end_date + datetime.timedelta(days=1)

    return sorted(set([
        d for d in [dateutil.parser.parse(s).date() for s in iso_dates]
        if __date_in_sprint(d)]))


## @note The output of this function shouldn't be dumped directly into json because of
#      the not serialized dates in it. If there is a need to dump it into json, some
#      additional serialize_team_capacity function should be added.
def process_team_capacity(sprint_data, capacity_data):
    sprint_start_date = dateutil.parser.parse(sprint_data["start date"]).date()
    sprint_end_date = dateutil.parser.parse(sprint_data["end date"]).date()
    workday_count = numpy.busday_count(sprint_start_date, sprint_end_date)

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
