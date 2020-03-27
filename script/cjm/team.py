"""Team data processing helpers"""

# Standard library imports
import json

# Third party imports
import jsonschema

# Project imports
import cjm.schema
import cjm.request


def load_data(cfg, team_file):
    """Load and validate given team data file"""
    schema = cjm.schema.load(cfg, "team.json")
    data = json.load(team_file)
    jsonschema.validate(data, schema)
    return data


# @param issues Any iterable with dict like items and at least an "assignee id" element in each
#     of these items. For reference see output of the cjm.sprint.request_issues_by_sprint
#     function.
# @param team_data Team data structure as returned by cjm.team.load_data
def filter_team_issues(cfg, issues, team_data):
    """Filter given issue list to exclude issues not assigned to team members

    There is an option to include unassigned issues
    """
    include_unassigned = cfg["issue"]["include unassigned"]
    valid_account_id_list = (
        [r["account id"] for r in team_data["people"]] +
        ([None] if include_unassigned else []))

    return [i for i in issues if i["assignee id"] in valid_account_id_list]


def format_full_name(person):
    """Format person full name"""
    return "{0:s}, {1:s}".format(person["last name"], person["first name"])
