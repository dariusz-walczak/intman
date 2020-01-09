#!/usr/bin/env python3

# Standard library imports
import os.path
import sys

# Third party imports
import dateutil.parser
import requests
import simplejson
import tabulate

# Project imports
import cjm
import cjm.cfg


DEFAULTS_FILE_NAME = ".cjm.json"


def parse_options(args):
    defaults = cjm.load_defaults()
    parser = cjm.make_common_parser(defaults)

    default_sprint_id = defaults.get("sprint", {}).get("id")
    sprint_arg_name = "sprint"

    parser.add_argument(
        "--{0:s}".format(sprint_arg_name), action="store", type=int, metavar="ID", dest="sprint_id",
        default=default_sprint_id,
        help=(
            "IDentifier of the sprint to list the issues for{0:s}"
            "".format(cjm.fmt_dft(default_sprint_id))))

    options = parser.parse_args(args)

    if (options.sprint_id is None):
        parser.error(
            "Missing sprint id. Use the '--{0:s}' option or the defaults file to specify it"
            "".format(sprint_arg_name))

    return options


def main(options):
    cfg = cjm.cfg.apply_options(cjm.cfg.init_default(), options)
    cfg["sprint"]["id"] = options.sprint_id

    response = requests.get(
        cjm.make_cj_agile_url(cfg, "sprint/{0:d}/issue".format(cfg["sprint"]["id"])),
        params={"startAt": 10},
        auth=(cfg["jira"]["user"]["name"], cfg["jira"]["user"]["token"])
    )

    issues = []

    import pdb; pdb.set_trace()

    for issue in response.json()["issues"]:
        #project_key = cfg["project"]["key"]

        issue_data = {
            "id": issue["id"],
            "key": issue["key"],
            "summary": issue["fields"]["summary"]
        }
        issues.append(issue_data)
            
#        if (issue["originBoardId"] == cfg["board"]["id"]):
#            issue_data = {
#                "id": issue["id"],
#                "name": issue["name"],
#                "start_date": dateutil.parser.parse(issue["startDate"]),
#                "end_date": dateutil.parser.parse(issue["endDate"]),
#                "complete_date": (
#                    dateutil.parser.parse(issue["completeDate"])
#                    if "completeDate" in issue
#                    else None),
#                "state": issue["state"]
#            }
#            issues.append(issue_data)


    if options.json_output:
        print(simplejson.dumps(issues, indent=4, sort_keys=False))
    else:
        print(tabulate.tabulate(
            [(i["id"], i["key"], i["summary"]) for i in issues],
            headers=["Id", "Key", "Summary"], tablefmt="orgtbl"))

    return 0


if __name__ == '__main__':
    sys.exit(main(parse_options(sys.argv[1:])))
