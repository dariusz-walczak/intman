# SPDX-License-Identifier: MIT
# Copyright (C) 2020-2021 Mobica Limited

"""Sprint data processing helpers"""

# Standard imports
import datetime
import json

# Third party imports
import jsonschema

# Project imports
import cjm.data
import cjm.issue
import cjm.schema
import cjm.request
import cjm.codes


def apply_data_file_paths(cfg, sprint_data):
    """Apply sprint data file paths taken from sprint data to the execution context (cfg)"""
    def __apply_data_file_path(cfg, variant, default):
        if cfg["path"][variant] is None:
            cfg["path"][variant] = sprint_data.get("file", {}).get(variant, default)
        return cfg

    cfg = __apply_data_file_path(cfg, "team", "team.json")
    cfg = __apply_data_file_path(
        cfg, "capacity", cjm.data.make_default_file_name(cfg, sprint_data, "capacity"))
    cfg = __apply_data_file_path(
        cfg, "commitment", cjm.data.make_default_file_name(cfg, sprint_data, "commitment"))
    cfg = __apply_data_file_path(
        cfg, "delivery", cjm.data.make_default_file_name(cfg, sprint_data, "delivery"))
    return cfg


def get_iso_week(date):
    """Determine ISO week number"""
    return date.isocalendar()[1]


def get_us_week(date):
    """Determine US (North American) week number"""
    # Each date belongs to some week. Each week has a Saturday. The week_sat_offset is number of
    # days between the Saturday and the date:
    week_sat_offset = (12 - date.weekday()) % 7
    week_sat = date + datetime.timedelta(days=week_sat_offset)
    week_year = week_sat.year

    frst_sat_offset = (12 - datetime.date(week_year, 1, 1).weekday()) % 7
    frst_sat = datetime.date(week_year, 1, 1) + datetime.timedelta(days=frst_sat_offset)

    return (((date - frst_sat).days - 1) // 7) + 2


def get_week(cfg, date):
    """
    Determine week number in the system defined by the calendar.week.system configuration
    variable
    """
    if cfg["calendar"]["week"]["system"] == cjm.cfg.CALENDAR_WEEK_SYSTEM_NORTH_AMERICAN:
        return get_us_week(date)
    else:
        return get_iso_week(date)


def get_monday(cfg, date):
    """
    Determine date of a monday belonging to the same week as given date
    """
    if cfg["calendar"]["week"]["system"] == cjm.cfg.CALENDAR_WEEK_SYSTEM_NORTH_AMERICAN:
        return date + datetime.timedelta(days=(1-((date.weekday()+1)%7)))
    else:
        return date - datetime.timedelta(days=date.weekday())


def generate_sprint_period_name(cfg, start_dt, end_dt):
    """Generate a standard sprint period name in form of WWxx-WWyy or WWzz and depending on given
    time range"""

    start_dt = start_dt + datetime.timedelta(days=cfg["calendar"]["week"]["name"]["lower offset"])
    end_dt = end_dt + datetime.timedelta(days=cfg["calendar"]["week"]["name"]["upper offset"])

    start_ww = get_week(cfg, start_dt)
    end_ww = get_week(cfg, end_dt)

    if start_ww != end_ww:
        return "WW{0:02d}-WW{1:02d}".format(start_ww, end_ww)
    else:
        return "WW{0:02d}".format(start_ww)


def generate_sprint_name(cfg, project_name, start_dt, end_dt):
    """Generate a standard sprint name"""
    return "{0:s} {1:s}".format(project_name, generate_sprint_period_name(cfg, start_dt, end_dt))


def load_data(cfg, sprint_file):
    """Load and validate given sprint data file"""
    schema = cjm.schema.load(cfg, "sprint.json")
    data = json.load(sprint_file)
    jsonschema.validate(data, schema)
    return data


def request_issues_by_sprint(cfg):
    """Request all issues associated with given sprint"""
    issues = []

    sprint_issues_url = cjm.request.make_cj_agile_url(
        cfg, "sprint/{0:d}/issue".format(cfg["sprint"]["id"]))

    start_at = 0
    max_results = 50

    while True:
        response = cjm.request.make_cj_request(
            cfg, sprint_issues_url,
            {"startAt": start_at, "maxResults": max_results})
        response_json = response.json()

        for issue in response_json["issues"]:
            issues.append(cjm.issue.extract_issue_data(cfg, issue))

        start_at += max_results

        if start_at >= response_json["total"]:
            break

    return issues


def request_issues_by_comment(cfg, comment):
    """Request all issues with given comment"""
    issues = []

    sprint_issues_url = cjm.request.make_cj_url(cfg, "search")

    jql = 'project = "{0:s}" AND comment ~ "{1:s}"'.format(cfg["project"]["key"], comment)
    start_at = 0
    max_results = 50

    while True:
        response = cjm.request.make_cj_post_request(
            cfg, sprint_issues_url,
            json={"jql": jql, "startAt": start_at, "maxResults": max_results})
        response_json = response.json()

        for issue in response_json["issues"]:
            issues.append(cjm.issue.extract_issue_data(cfg, issue))

        start_at += max_results

        if start_at >= response_json["total"]:
            break

    return issues
