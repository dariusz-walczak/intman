#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Standard library imports
import sys
import json

# Third party imports
import requests
import tabulate

# Project imports
import cjm
import cjm.cfg
import cjm.request


DEFAULT_FILE = ".cjm.json"


def parse_options(args):
    defaults = cjm.cfg.load_defaults()
    parser = cjm.cfg.make_common_parser(defaults)

    default_sprint_id = defaults.get("sprint", {}).get("id")
    sprint_arg_name = "sprint"

    parser.add_argument(
        "--{0:s}".format(sprint_arg_name), action="store", type=int, metavar="ID", dest="sprint_id",
        default=default_sprint_id,
        help=(
            "IDentifier of the sprint to list the issues for{0:s}"
            "".format(cjm.cfg.fmt_dft(default_sprint_id))))

    options = parser.parse_args(args)

    if options.sprint_id is None:
        parser.error(
            "Missing sprint id. Use the '--{0:s}' option or the defaults file to specify it"
            "".format(sprint_arg_name))

    return options


def main(options):
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)
    cfg["sprint"]["id"] = options.sprint_id

    response = requests.get(
        cjm.request.make_cj_agile_url(cfg, "sprint/{0:d}/issue".format(cfg["sprint"]["id"])),
        params={"startAt": 0},
        auth=(cfg["jira"]["user"]["name"], cfg["jira"]["user"]["token"])
    )

    issues = []

    for issue in response.json()["issues"]:
        issue_data = {
            "id": issue["id"],
            "key": issue["key"],
            "summary": issue["fields"]["summary"]
        }
        issues.append(issue_data)

    if options.json_output:
        print(json.dumps(issues, indent=4, sort_keys=False))
    else:
        print(tabulate.tabulate(
            [(i["id"], i["key"], i["summary"]) for i in issues],
            headers=["Id", "Key", "Summary"], tablefmt="orgtbl"))

    return 0


if __name__ == '__main__':
    sys.exit(main(parse_options(sys.argv[1:])))
