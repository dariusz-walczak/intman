#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Standard library imports
import copy
import decimal
import json
import re
import sys
import datetime
import bisect

# Third party imports
import jsonschema
import tabulate
import dateutil.parser

# Project imports
import cjm
import cjm.cfg
import cjm.codes
import cjm.commitment
import cjm.issue
import cjm.schema
import cjm.sprint
import cjm.team


def parse_options(args):
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
        "commitment_file", action="store",
        help=(
            "Path to the json commitment data file as generated by the {0:s} script and described"
            " by the {1:s} schema"
            "".format(cjm.SM_CREATE_COMMITMENT_FILE, cjm.schema.make_subpath("commitment.json"))))
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
    result_code, issues = cjm.issue.request_issues_by_keys(cfg, issue_keys)

    if result_code:
        return result_code

    response_keys = set([i["key"] for i in issues])
    request_keys = set(issue_keys)

    if response_keys != request_keys:
        sys.stderr.write(
            "WARNING: Following issues were requested but not included in the response ({0:s})\n"
            "".format(", ".join(sorted(request_keys-response_keys))))

    augment_cb = _make_augment_issue_cb(cfg, False)
    return cjm.codes.NO_ERROR, [augment_cb(i) for i in issues]


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



def main(options):
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)
    cfg["issue"]["include unassigned"] = True

    # Load sprint data:

    try:
        with open(options.sprint_file) as sprint_file:
            sprint_data = cjm.sprint.load_data(cfg, sprint_file)
    except IOError as e:
        sys.stderr.write(
            "ERROR: Sprint data file ('{0:s}') I/O error\n".format(options.sprint_file))
        sys.stderr.write("    {0}\n".format(e))
        return cjm.codes.FILESYSTEM_ERROR

    sprint_schema = cjm.schema.load(cfg, "sprint.json")
    jsonschema.validate(sprint_data, sprint_schema)

    cfg["sprint"]["id"] = sprint_data.get("id")
    cfg["project"]["key"] = sprint_data["project"]["key"]


    if cfg["sprint"]["id"] is None:
        sys.stderr.write(
            "ERROR: The sprint id is not specified by the sprint data file ('{0:s}')\n"
            "".format(options.sprint_file))
        return cjm.codes.CONFIGURATION_ERROR

    # Load team data:

    try:
        with open(options.team_file) as team_file:
            team_data = cjm.team.load_data(cfg, team_file)
    except IOError as e:
        sys.stderr.write(
            "ERROR: Team data file ('{0:s}') I/O error\n".format(options.team_file))
        sys.stderr.write("    {0}\n".format(e))
        return cjm.codes.FILESYSTEM_ERROR

    team_schema = cjm.schema.load(cfg, "team.json")
    jsonschema.validate(team_data, team_schema)

    # Load commitment data:

    try:
        with open(options.commitment_file) as commitment_file:
            commitment_data = cjm.commitment.load_data(cfg, commitment_file)
    except IOError as e:
        sys.stderr.write(
            "ERROR: Commitment data file ('{0:s}') I/O error\n".format(options.commitment_file))
        sys.stderr.write("    {0}\n".format(e))
        return cjm.codes.FILESYSTEM_ERROR

    commitment_schema = cjm.schema.load(cfg, "commitment.json")
    jsonschema.validate(commitment_data, commitment_schema)

    # Determine the story points field id:

    if cfg["jira"]["fields"]["story points"] is None:
        cfg["jira"]["fields"]["story points"] = cjm.issue.detect_story_point_field_id(cfg)

    # Request all committed issues:

    result_code, issues_com = _retrieve_issues(cfg, [i["key"] for i in commitment_data["issues"]])

    if result_code:
        return result_code

    # Request all extension issues and determine their commitment story points:

    issues_ext = _retrieve_extension_issues(cfg, sprint_data, team_data)

    issues = sorted(_join_issue_lists(issues_com, issues_ext), key=lambda i: i["id"])

    # Request dropped issues and change story point value to 0
    issues_drp = cjm.sprint.request_issues_by_comment(
        cfg, "{0:s}/Dropped".format(sprint_data["comment prefix"]))

    for iss in issues_drp:
        dropped_issue = bisect.bisect([i["id"] for i in issues], iss["id"])

        if dropped_issue > len(issues):
            sys.stderr.write(
                "WARNING: Issue {0:s} has dropped comment for this sprint,"
                " but it doesn't appear to be in commited or extended issues\n"
                "".format(iss["id"]))
        else:
            issues[dropped_issue-1]["dropped"] = True


    sprint_end_date = dateutil.parser.parse(sprint_data["end date"]).date()
    sprint_end_date = sprint_end_date + datetime.timedelta(days=1)

    issues_delivered = []
    if options.delivery_comment:
        issues_delivered = cjm.sprint.request_issues_by_comment(
            cfg, "{0:s}/Delivered".format(sprint_data["comment prefix"]))

    delivered_issues_ids = [i["id"] for i in issues_delivered]
    def __issue_done(issue):
        if options.delivery_comment and issue["id"] in delivered_issues_ids:
            return True

        if issue["status"] != "Done" or issue["resolution date"] is None:
            return False

        issue_resolve_date = dateutil.parser.parse(issue["resolution date"]).date()
        return issue_resolve_date < sprint_end_date

    # Determine delivered story points

    for issue in issues:
        issue["delivered"] = __issue_done(issue)

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

    total_committed = sum([i["committed story points"] for i in issues])
    total_delivered = sum([i["story points"] for i in issues if __issue_done(i)])

    delivery_ratio = decimal.Decimal(total_delivered) / decimal.Decimal(total_committed)
    delivery_ratio = delivery_ratio.quantize(decimal.Decimal(".0000"), decimal.ROUND_HALF_UP)

    report = {
        "total": {
            "committed": total_committed,
            "delivered": total_delivered
        },
        "ratio": str(delivery_ratio),
        "issues": issues,
    }

    delivery_schema = cjm.schema.load(cfg, "delivery.json")
    jsonschema.validate(report, delivery_schema)

    if options.json_output:
        print(json.dumps(report, indent=4, sort_keys=False))
    else:
        if options.show_summary:
            print_summary(report, team_data)
        else:
            print_issue_list(report, team_data)

    return cjm.codes.NO_ERROR


def print_issue_list(delivery, team_data):
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


def print_summary(delivery, team_data):
    pass


if __name__ == '__main__':
    sys.exit(main(parse_options(sys.argv[1:])))
