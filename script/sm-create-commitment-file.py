#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line script creating sprint commitment report file"""

# Standard library imports
import json
import sys

# Third party imports
import jsonschema
import tabulate

# Project imports
import cjm
import cjm.capacity
import cjm.commitment
import cjm.cfg
import cjm.codes
import cjm.data
import cjm.issue
import cjm.request
import cjm.run
import cjm.schema
import cjm.sprint
import cjm.team


def parse_options(args):
    """Parse command line options"""
    defaults = cjm.cfg.load_defaults()
    parser = cjm.cfg.make_common_parser(defaults)

    parser.add_argument(
        "sprint_file", action="store",
        help=(
            "Path to the json sprint data file as generated by the {0:s} script and described by"
            " the {1:s} schema"
            "".format(cjm.SM_CREATE_SPRINT_FILE, cjm.schema.make_subpath("sprint.json"))))

    parser.add_argument(
        "--include-unassigned", action="store_true", dest="include_unassigned", default=False,
        help="Include unassigned issues in the issue list")
    parser.add_argument(
        "--estimated", action="store", dest="estimated_filter", choices=("all", "yes", "no"),
        default="all", help="Filter the issues by the fact of being or not being estimated")
    parser.add_argument(
        "--commented", action="store", dest="comment_filter", choices=("all", "yes", "no"),
        default="all", help=(
            "Filter the issues by the fact of them having or not having the commitment comment"))
    parser.add_argument(
        "--associated", action="store", dest="sprint_filter", choices=("all", "yes", "no"),
        default="all", help=(
            "Filter the issues by the fact of them being associated with the sprint"))
    parser.add_argument(
        "-s", "--summary", action="store_true", dest="show_summary", default=False,
        help="Show the commitment summary instead of the detailed issue table")

    return parser.parse_args(args)


def _process_sprint_issues(cfg, team_data):
    issues_all = cjm.sprint.request_issues_by_sprint(cfg)
    issues_team = cjm.team.filter_team_issues(cfg, issues_all, team_data)

    for issue in issues_team:
        issue["by sprint"] = True
        issue["by comment"] = False

    return dict((i["id"], i) for i in issues_team)


def _process_commented_issues(cfg, sprint_data, team_data, issue_lut, comment_postfix):
    issues_all = cjm.sprint.request_issues_by_comment(
        cfg, "{0:s}/{1:s}".format(sprint_data["comment prefix"], comment_postfix))
    issues_team = cjm.team.filter_team_issues(cfg, issues_all, team_data)

    for issue in issues_team:
        issue_id = issue["id"]
        if issue_id in issue_lut:
            issue_lut[issue_id]["by comment"] = True
        else:
            issue_lut[issue_id] = issue
            issue_lut[issue_id]["by sprint"] = False
            issue_lut[issue_id]["by comment"] = True

    return issue_lut


def main(options):
    """Entry function"""
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)
    cfg["issue"]["include unassigned"] = options.include_unassigned

    # Load sprint data:

    sprint_data = cjm.data.load(cfg, options.sprint_file, "sprint.json")

    cfg["sprint"]["id"] = sprint_data.get("id")
    cfg["project"]["key"] = sprint_data["project"]["key"]

    if cfg["sprint"]["id"] is None:
        sys.stderr.write(
            "ERROR: The sprint id is not specified by the sprint data file ('{0:s}')\n"
            "".format(options.sprint_file))
        return cjm.codes.CONFIGURATION_ERROR

    cjm.sprint.apply_data_file_paths(cfg, sprint_data)

    # Load other data:

    team_data = cjm.data.load(cfg, cfg["path"]["team"], "team.json")
    capacity_data = cjm.data.load(cfg, cfg["path"]["capacity"], "capacity.json")

    # Determine the story points field id:

    if cfg["jira"]["fields"]["story points"] is None:
        cfg["jira"]["fields"]["story points"] = cjm.issue.detect_story_point_field_id(cfg)

    # Retrieve issues assigned to the sprint:

    issue_lut = _process_sprint_issues(cfg, team_data)

    # Retrieve issues with the commitment comment added:

    issue_lut = _process_commented_issues(cfg, sprint_data, team_data, issue_lut, "Committed")
    issue_lut = _process_commented_issues(cfg, sprint_data, team_data, issue_lut, "Extended")

    issues = [issue_lut[k] for k in sorted(issue_lut.keys())]
    issues = list(filter(
        cjm.data.make_defined_filter("story points", options.estimated_filter), issues))
    issues = list(filter(
        cjm.data.make_flag_filter("by comment", options.comment_filter), issues))
    issues = list(filter(
        cjm.data.make_flag_filter("by sprint", options.sprint_filter), issues))

    for issue in issues:
        if issue["story points"] is not None:
            issue["story points"] = int(issue["story points"])

    total_sp = sum(
        [i["story points"] for i in issue_lut.values()
         if i["story points"] is not None])
    commitment = {"total": {"committed": total_sp}, "issues": list(issues)}

    commitment_schema = cjm.schema.load(cfg, "commitment.json")
    jsonschema.validate(commitment, commitment_schema)

    if options.json_output:
        print(json.dumps(commitment, indent=4, sort_keys=False))
    else:
        if options.show_summary:
            print_summary(cfg, team_data, sprint_data, capacity_data, commitment)
        else:
            print_issue_list(commitment, team_data)


    return cjm.codes.NO_ERROR


def print_issue_list(commitment_data, team_data):
    """Print the detailed issue status table"""
    person_lut = dict((p["account id"], p) for p in team_data["people"])

    def __fmt_assignee(issue):
        if issue["assignee id"] is None:
            return ""
        return cjm.team.format_full_name(person_lut[issue["assignee id"]])

    print(tabulate.tabulate(
        [(i["id"], i["key"], i["summary"], __fmt_assignee(i), i["story points"],
          "Sprint" if i["by sprint"] else "",
          "Comment" if i["by comment"] else "",
          i["status"])
         for i in commitment_data["issues"]],
        headers=["Id", "Key", "Summary", "Assignee", "Story Points", "Sprint", "Comment", "Status"],
        tablefmt="orgtbl"))


def print_summary(cfg, team_data, sprint_data, capacity_data, commitment_data):
    """Print the report summary table"""
    person_capacity_list = cjm.capacity.process_person_capacity_list(sprint_data, capacity_data)
    person_capacity_lut = cjm.capacity.make_person_capacity_lut(person_capacity_list)
    total_capacity = sum(p["sprint capacity"] for p in person_capacity_list)

    assigned_commitment = cjm.commitment.calc_total(
        cjm.issue.assigned_issues(commitment_data["issues"]))
    unassigned_commitment = cjm.commitment.calc_total(
        cjm.issue.unassigned_issues(commitment_data["issues"]))

    cells = (
        cjm.presentation.default_cell("caption"),
        cjm.presentation.default_cell("commitment"),
        cjm.presentation.default_cell("capacity"),
        cjm.presentation.ratio_cell("commitment ratio"),
        cjm.presentation.status_cell("commitment status"))

    def __make_person_row(person_data):
        capacity = (
            person_capacity_lut.get(person_data["account id"], {}).get("sprint capacity", 0))
        commitment = cjm.commitment.calc_total(
            cjm.issue.person_issues(commitment_data["issues"], person_data))
        summary = cjm.capacity.determine_summary(commitment, capacity)

        if summary["capacity"] or summary["commitment"]:
            importance_code = cjm.presentation.IMPORTANCE_CODES.NORMAL
        else:
            importance_code = cjm.presentation.IMPORTANCE_CODES.LOW

        return cjm.presentation.format_row(
            importance_code, cells,
            {**summary, "caption": cjm.team.format_full_name(person_data)})


    def __make_unassigned_row():
        capacity = total_capacity - assigned_commitment
        summary = cjm.capacity.determine_summary(unassigned_commitment, capacity)

        if summary["commitment"]:
            importance_code = cjm.presentation.IMPORTANCE_CODES.NORMAL
        else:
            importance_code = cjm.presentation.IMPORTANCE_CODES.LOW

        return cjm.presentation.format_row(
            importance_code, cells, {**summary, "caption": "Unasigned"})

    def __make_total_row():
        commitment = assigned_commitment + unassigned_commitment
        summary = cjm.capacity.determine_summary(commitment, total_capacity)

        return cjm.presentation.format_row(
            cjm.presentation.IMPORTANCE_CODES.HIGH, cells,
            {**summary, "caption": "Team Summary"})

    def __sort_cb(person):
        return (person["last name"], person["first name"])

    print(tabulate.tabulate(
        [__make_person_row(p) for p in sorted(team_data["people"], key=__sort_cb)] +
        ([__make_unassigned_row()] if cfg["issue"]["include unassigned"] else []) +
        [__make_total_row()],
        headers=["Full Name", "Commitment", "Capacity", "Com/Cap Ratio", "Status"],
        tablefmt="orgtbl"))


if __name__ == '__main__':
    cjm.run.run(main, parse_options(sys.argv[1:]))
