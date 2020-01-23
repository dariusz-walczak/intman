#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Standard library imports
import sys
import json

# Third party imports
import dateutil.parser
import requests
import tabulate

# Project imports
import cjm
import cjm.cfg
import cjm.request

DEFAULTS_FILE_NAME = ".cjm.json"


def parse_options(args):
    defaults = cjm.cfg.load_defaults()
    parser = cjm.cfg.make_common_parser(defaults)

    default_board_id = defaults.get("board", {}).get("id")
    board_arg_name = "board"

    parser.add_argument(
        "--{0:s}".format(board_arg_name), action="store", type=int, metavar="ID", dest="board_id",
        default=default_board_id,
        help=(
            "IDentifier of the board to list the sprints for{0:s}"
            "".format(cjm.cfg.fmt_dft(default_board_id))))

    options = parser.parse_args(args)

    if options.board_id is None:
        parser.error(
            "Missing board id. Use the '--{0:s}' option or the defaults file to specify it"
            "".format(board_arg_name))

    return options


def __fmt_opt(v): return "" if v is None else str(v)


def main(options):
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)
    cfg["board"]["id"] = options.board_id

    response = requests.get(
        cjm.request.make_cj_agile_url(cfg, "board/{0:d}/sprint".format(cfg["board"]["id"])),
        auth=(cfg["jira"]["user"]["name"], cfg["jira"]["user"]["token"])
    )

    sprints = []

    for sprint in response.json()["values"]:
        # project_key = cfg["project"]["key"]

        if sprint["originBoardId"] == cfg["board"]["id"]:
            sprint_data = {
                "id": sprint["id"],
                "name": sprint["name"],
                "state": sprint["state"],
                "start_date": (
                    dateutil.parser.parse(sprint["startDate"]).date().isoformat()
                    if "startDate" in sprint
                    else None),
                "end_date": (
                    dateutil.parser.parse(sprint["endDate"]).date().isoformat()
                    if "endDate" in sprint
                    else None),
                "complete_date": (
                    dateutil.parser.parse(sprint["completeDate"]).date().isoformat()
                    if "completeDate" in sprint
                    else None)
            }
            sprints.append(sprint_data)

    if options.json_output:
        print(json.dumps(sprints, indent=4, sort_keys=False))
    else:

        # Do not assign a lambda expression, use a def (E731)
        # https://www.flake8rules.com/rules/E731.html
        # __fmt_opt = lambda v: "" if v is None else str(v)

        print(tabulate.tabulate(
            [(s["id"], s["name"], s["state"], __fmt_opt(s["start_date"]), __fmt_opt(s["end_date"]))
             for s in sprints],
            headers=["Id", "Name", "State", "Start", "End"], tablefmt="orgtbl"))

    return 0


if __name__ == '__main__':
    sys.exit(main(parse_options(sys.argv[1:])))
