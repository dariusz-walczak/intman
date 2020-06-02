#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line script creating sprint delivery report file"""

# Standard library imports
import copy
import decimal
import json
import re
import sys
import datetime

# Third party imports
import jsonschema
import tabulate
import dateutil.parser

# Project imports
import cjm
import cjm.capacity
import cjm.cfg
import cjm.codes
import cjm.commitment
import cjm.data
import cjm.delivery
import cjm.issue
import cjm.presentation
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
        "team_file", action="store",
        help=(
            "Path to the json team data file as generated by the {0:s} script and described by"
            " the {1:s} schema"
            "".format(cjm.SM_CREATE_TEAM_FILE, cjm.schema.make_subpath("team.json"))))
    parser.add_argument(
        "capacity_file", action="store",
        help=(
            "Path to the json capacity data file as generated by the {0:s} script and described"
            " by the {1:s} schema"
            "".format(cjm.SM_CREATE_CAPACITY_FILE, cjm.schema.make_subpath("capacity.json"))))
    parser.add_argument(
        "commitment_file", action="store",
        help=(
            "Path to the json commitment data file as generated by the {0:s} script and described"
            " by the {1:s} schema"
            "".format(cjm.SM_CREATE_COMMITMENT_FILE, cjm.schema.make_subpath("commitment.json"))))
    parser.add_argument(
        "--delivered", action="store", dest="delivered_filter", choices=("all", "yes", "no"),
        default="all",
        help="Filter the issues by the delivered flag")
    parser.add_argument(
        "--consider-delivery-comment", action="store_true", dest="delivery_comment",
        help="Add to raport ticket closed after sprint but with comment /Delivered")
    parser.add_argument(
        "-s", "--summary", action="store_true", dest="show_summary", default=False,
        help="Show the delivery summary instead of the detailed issue table")
    return parser.parse_args(args)


def _make_augment_issue_cb(cfg, extended, sprint_data=None):
    if extended:
        ext_comment_re = re.compile(
            r"{0:s}/Extended \((?P<committed>[0-9]+)/(?P<deliverable>[0-9]+)\)"
            "".format(re.escape(sprint_data["comment prefix"]))) if extended else None
        assert sprint_data is not None

    def __retrieve_ext_committed_sps(issue):
        result_code, comments = \
            cjm.issue.request_issue_comments_regexp(cfg, issue["key"], ext_comment_re)

        if result_code:
            raise cjm.codes.CjmError(result_code)

        if not comments:
            return 0
        else:
            if len(set(comments)) > 1:
                sys.stderr.write(
                    "WARNING: Issue '{0:s}' has more than one sprint extension comment. Only"
                    " the first meaningful one will be used. Delete all erroneous comments"
                    " for the sprint '{1:s}'\n"
                    "".format(issue["key"], sprint_data["comment prefix"]))
            sp_committed = int(comments[0].group("committed"))
            sp_deliverable = int(comments[0].group("deliverable"))
            if sp_deliverable != issue["story points"]:
                sys.stderr.write(
                    "WARNING: Regarding issue {0:s}: Story point value inconsistency between"
                    " the story points field ({1:d}) and the sprint extension comment"
                    " ({2:d}/{3:d}). The value taken from the story points field will be used"
                    " for reporting purposes and the committed value will be assumed to be 0\n"
                    "".format(issue["key"], issue["story points"], sp_committed, sp_deliverable))
                return 0
            elif sp_committed > sp_deliverable:
                sys.stderr.write(
                    "WARNING: Regarding issue {0:s}: According to the sprint extension"
                    " comment, the number of committed story points ({1:d}) is greater than"
                    " the number of deliverable story points ({2:d}). The deliverable number"
                    " of story points will be used in both cases\n"
                    "".format(issue["key"], sp_committed, sp_deliverable))
                return sp_deliverable
            else:
                return sp_committed

    def __augment_issue_cb(issue):
        issue = copy.copy(issue)
        points = issue.get("story points")
        points = 0 if points is None else int(points)
        issue["story points"] = points
        issue["dropped"] = False
        issue["extended"] = extended
        issue["committed story points"] = (
            __retrieve_ext_committed_sps(issue) if extended else points)
        issue["delivered story points"] = -1
        return issue

    return __augment_issue_cb

def _retrieve_issues(cfg, issue_keys):
    issues = cjm.issue.request_issues_by_keys(cfg, issue_keys)

    response_keys = set([i["key"] for i in issues])
    request_keys = set(issue_keys)

    if response_keys != request_keys:
        sys.stderr.write(
            "WARNING: Following issues were requested but not included in the response ({0:s})\n"
            "".format(", ".join(sorted(request_keys-response_keys))))

    augment_cb = _make_augment_issue_cb(cfg, False)
    return [augment_cb(i) for i in issues]


def _retrieve_extension_issues(cfg, sprint_data, team_data):
    issues = cjm.sprint.request_issues_by_comment(
        cfg, "{0:s}/Extended".format(sprint_data["comment prefix"]))
    augment_cb = _make_augment_issue_cb(cfg, True, sprint_data)
    return [augment_cb(i) for i in cjm.team.filter_team_issues(cfg, issues, team_data)]


def _join_issue_lists(issues_com, issues_ext):
    com_keys = [i["key"] for i in issues_com]

    def __ext_issue_uniq(issue):
        if issue["key"] in com_keys:
            sys.stderr.write(
                "WARNING: Issue '{0:s}' was found in the commitment data file and at the same"
                " time it was found out to be marked with sprint extension comment. The comment"
                " will be ignored\n".format(issue["key"]))
            return False
        else:
            return True

    return issues_com + [i for i in issues_ext if __ext_issue_uniq(i)]


def _process_dropped_issues(cfg, sprint_data, all_issues):
    """Determine dropped status of given issues"""
    issues_drp = cjm.sprint.request_issues_by_comment(
        cfg, "{0:s}/Dropped".format(sprint_data["comment prefix"]))

    issue_lut = {i["id"]: i for i in all_issues}

    for dropped_issue in issues_drp:
        issue = issue_lut.get(dropped_issue["id"])

        if issue is None:
            sys.stderr.write(
                "WARNING: An issue ({0:s}) has been found to have the dropped comment but no"
                " corresponding committed or extended comment\n".format(dropped_issue["id"]))
        else:
            issue["dropped"] = True

    return all_issues


def _process_delivered_issues(cfg, sprint_data, all_issues):
    """Determine delivery status of given issues.

    Optionally, allow late delivery issues, i.e. issues that were delivered after the sprint end
    but still contain (manually added) `/Delivered` comment
    """
    if cfg["issue"]["allow late delivery"]:
        issues_delivered = cjm.sprint.request_issues_by_comment(
            cfg, "{0:s}/Delivered".format(sprint_data["comment prefix"]))

        delivered_ids = [i["id"] for i in issues_delivered]
    else:
        delivered_ids = []

    sprint_end_date = (
        dateutil.parser.parse(sprint_data["end date"]).date() + datetime.timedelta(days=1))

    def __issue_done(issue):
        if issue["id"] in delivered_ids:
            return True

        if issue["status"] != "Done" or issue["resolution date"] is None:
            return False

        issue_resolve_date = dateutil.parser.parse(issue["resolution date"]).date()
        return issue_resolve_date < sprint_end_date

    return [{**i, "delivered": __issue_done(i)} for i in all_issues]


def _make_delivery_data(all_issues):
    for issue in all_issues:
        if issue["dropped"]:
            issue["committed story points"] = 0
            issue["delivered story points"] = 0
            issue["outcome"] = "drop"
        elif issue["delivered"]:
            issue["delivered story points"] = issue["story points"]
            issue["outcome"] = "done"
        else:
            issue["delivered story points"] = 0
            issue["outcome"] = "open"

        issue["income"] = "extend" if issue["extended"] else "commit"

    total_committed = sum([i["committed story points"] for i in all_issues])
    total_delivered = sum([i["delivered story points"] for i in all_issues if i["delivered"]])

    if total_committed > 0:
        delivery_ratio = decimal.Decimal(total_delivered) / decimal.Decimal(total_committed)
        delivery_ratio = delivery_ratio.quantize(decimal.Decimal(".0000"), decimal.ROUND_HALF_UP)
        ratio_value = str(delivery_ratio)
    else:
        ratio_value = None

    return {
        "total": {
            "committed": total_committed,
            "delivered": total_delivered
        },
        "ratio": ratio_value,
        "issues": sorted(all_issues, key=lambda i: i["id"])
    }


def main(options):
    """Entry function"""
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)
    cfg["issue"]["include unassigned"] = True
    cfg["issue"]["allow late delivery"] = options.delivery_comment

    # Load sprint data:

    sprint_data = cjm.data.load(cfg, options.sprint_file, "sprint.json")

    cfg["sprint"]["id"] = sprint_data.get("id")
    cfg["project"]["key"] = sprint_data["project"]["key"]


    if cfg["sprint"]["id"] is None:
        sys.stderr.write(
            "ERROR: The sprint id is not specified by the sprint data file ('{0:s}')\n"
            "".format(options.sprint_file))
        return cjm.codes.CONFIGURATION_ERROR

    # Load other data:

    team_data = cjm.data.load(cfg, options.team_file, "team.json")
    capacity_data = cjm.data.load(cfg, options.capacity_file, "capacity.json")
    commitment_data = cjm.data.load(cfg, options.commitment_file, "commitment.json")

    # Determine the story points field id:

    if cfg["jira"]["fields"]["story points"] is None:
        cfg["jira"]["fields"]["story points"] = cjm.issue.detect_story_point_field_id(cfg)

    # Request all committed issues:

    issues_com = _retrieve_issues(cfg, [i["key"] for i in commitment_data["issues"]])

    # Request all extension issues and determine their commitment story points:

    issues_ext = _retrieve_extension_issues(cfg, sprint_data, team_data)

    issues = _join_issue_lists(issues_com, issues_ext)

    # Request dropped issues and change story point value to 0

    issues = _process_dropped_issues(cfg, sprint_data, issues)
    issues = _process_delivered_issues(cfg, sprint_data, issues)
    issues = list(filter(cjm.data.make_flag_filter("delivered", options.delivered_filter), issues))

    # Determine delivered story points

    delivery_data = _make_delivery_data(issues)
    delivery_schema = cjm.schema.load(cfg, "delivery.json")
    jsonschema.validate(delivery_data, delivery_schema)

    if options.json_output:
        print(json.dumps(delivery_data, indent=4, sort_keys=False))
    else:
        if options.show_summary:
            print_summary(delivery_data, team_data, sprint_data, capacity_data)
        else:
            print_issue_list(delivery_data, team_data)

    return cjm.codes.NO_ERROR


def print_issue_list(delivery, team_data):
    """Print the detailed issue status table"""
    person_lut = dict((p["account id"], p) for p in team_data["people"])

    def __fmt_assignee(issue):
        if issue["assignee id"] is None:
            return ""
        else:
            return "{0:s}, {1:s}".format(
                person_lut[issue["assignee id"]]["last name"],
                person_lut[issue["assignee id"]]["first name"])

    print(tabulate.tabulate(
        [(i["id"], i["key"], i["summary"], __fmt_assignee(i),
          i["committed story points"], i["delivered story points"], i["status"],
          i["income"], i["outcome"], i["extended"], i["delivered"], i["dropped"])
         for i in delivery["issues"]],
        headers=["Id", "Key", "Summary", "Assignee", "Committed", "Delivered",
                 "Current Status", "Income", "Outcome", "Extended", "Delivered", "Dropped"],
        tablefmt="orgtbl"))


def calc_total(issues, field_key):
    """Calculate sum of given fields"""
    return sum([int(i[field_key]) for i in issues])


def print_summary(delivery_data, team_data, sprint_data, capacity_data):
    """Print the report summary table"""
    person_capacity_lut = cjm.capacity.make_person_capacity_lut(sprint_data, capacity_data)
    total_capacity = sum(p["sprint capacity"] for p in person_capacity_lut.values())
    total_committed = delivery_data["total"]["committed"]
    total_delivered = delivery_data["total"]["delivered"]

    unassigned_issues = cjm.issue.unassigned_issues(delivery_data["issues"])
    assigned_issues = cjm.issue.assigned_issues(delivery_data["issues"])

    assigned_committed = calc_total(assigned_issues, "committed story points")
    unassigned_committed = calc_total(unassigned_issues, "committed story points")

    cells = (
        cjm.presentation.default_cell("caption"),
        cjm.presentation.default_cell("delivery"),
        cjm.presentation.default_cell("commitment"),
        cjm.presentation.default_cell("capacity"),
        cjm.presentation.ratio_cell("commitment ratio"),
        cjm.presentation.status_cell("commitment status"),
        cjm.presentation.ratio_cell("delivery ratio"),
        cjm.presentation.status_cell("delivery status"))

    def __make_person_row(person_data):
        capacity = (
            person_capacity_lut.get(person_data["account id"], {}).get("sprint capacity", 0))
        commitment = calc_total(
            cjm.issue.person_issues(delivery_data["issues"], person_data),
            "committed story points")
        delivery = calc_total(
            cjm.issue.person_issues(delivery_data["issues"], person_data),
            "delivered story points")
        commitment_summary = cjm.capacity.determine_summary(commitment, capacity)
        delivery_summary = cjm.delivery.determine_summary(delivery, commitment)

        if commitment_summary["capacity"] or delivery_summary["commitment"]:
            importance_code = cjm.presentation.IMPORTANCE_CODES.NORMAL
        else:
            importance_code = cjm.presentation.IMPORTANCE_CODES.LOW

        return cjm.presentation.format_row(
            importance_code, cells,
            {**commitment_summary, **delivery_summary,
             "caption": cjm.team.format_full_name(person_data)})

    def __make_unassigned_row():
        capacity = total_capacity - assigned_committed
        commitment_summary = cjm.capacity.determine_summary(unassigned_committed, capacity)
        commitment = unassigned_committed
        delivery = calc_total(unassigned_issues, "delivered story points")
        delivery_summary = cjm.delivery.determine_summary(delivery, commitment)

        if delivery_summary["commitment"]:
            importance_code = cjm.presentation.IMPORTANCE_CODES.NORMAL
        else:
            importance_code = cjm.presentation.IMPORTANCE_CODES.LOW

        return cjm.presentation.format_row(
            importance_code, cells,
            {**commitment_summary, **delivery_summary, "caption": "Unasigned"})

    def __make_total_row():
        commitment_summary = cjm.capacity.determine_summary(total_committed, total_capacity)
        delivery_summary = cjm.delivery.determine_summary(total_delivered, total_committed)

        return cjm.presentation.format_row(
            cjm.presentation.IMPORTANCE_CODES.HIGH, cells,
            {**commitment_summary, **delivery_summary, "caption": "Team Summary"})

    def __sort_cb(person):
        return (person["last name"], person["first name"])

    print(tabulate.tabulate(
        [__make_person_row(p) for p in sorted(team_data["people"], key=__sort_cb)] +
        [__make_unassigned_row()] +
        [__make_total_row()],
        headers=[
            "Full Name", "Delivery", "Commitment", "Capacity",
            "Com/Cap Ratio", "Com Status", "Del/Com Ratio", "Del Status"],
        tablefmt="orgtbl"))

if __name__ == '__main__':
    cjm.run.run(main, parse_options(sys.argv[1:]))
