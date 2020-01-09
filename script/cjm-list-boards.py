#!/usr/bin/env python3

# Standard library imports
import os.path
import sys

# Third party imports
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

    default_project_key = defaults.get("project", {}).get("key")

    parser.add_argument(
        "--project-key", action="store", metavar="KEY", dest="project_key",
        default=default_project_key,
        help=(
            "Project to list the boards for{0:s}"
            "".format(cjm.fmt_dft(default_project_key))))
    parser.add_argument(
        "--all", action="store_true", dest="all_boards",
        help="List boards for all projects (overrides --project-key)")

    return parser.parse_args(args)


def main(options):
    cfg = cjm.cfg.apply_options(cjm.cfg.init_default(), options)
    cfg["project"]["key"] = options.project_key

    response = requests.get(
        cjm.make_cj_agile_url(cfg, "board"),
        auth=(cfg["jira"]["user"]["name"], cfg["jira"]["user"]["token"])
    )

    boards = []

    for board in response.json()["values"]:
        project_key = cfg["project"]["key"]

        if ((project_key is None) or options.all_boards or
            (project_key == board["location"]["projectKey"])):

            board_data = {
                "id":   board["id"],
                "name": board["name"]
            }
            boards.append(board_data)


    if options.json_output:
        print(simplejson.dumps(boards, indent=4, sort_keys=False))
    else:
        print(tabulate.tabulate(
            [(b["id"], b["name"]) for b in boards],
            headers=["Id", "Name"], tablefmt="orgtbl"))

    return 0


if __name__ == '__main__':
    sys.exit(main(parse_options(sys.argv[1:])))
