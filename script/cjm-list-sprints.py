#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright © 2020-2021 Mobica Limited. All rights reserved.

"""Command line script listing all sprints related to given board"""

# Standard library imports
import sys
import json

# Third party imports
import dateutil.parser
import tabulate

# Project imports
import cjm
import cjm.cfg
import cjm.request

DEFAULT_FILE = ".cjm.json"


def parse_options(args):
    """Parse command line options"""
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


def main(options):
    """Entry function"""
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)
    cfg["board"]["id"] = options.board_id

    start_at = 0
    max_results = 50
    url = cjm.request.make_cj_agile_url(cfg, "board/{0:d}/sprint".format(cfg["board"]["id"]))

    sprints = []

    while True:
        response = cjm.request.make_cj_request(
            cfg, url, {"startAt": start_at, "maxResults": max_results})
        response_json = response.json()

        for sprint in response_json["values"]:
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

        if response_json["isLast"]:
            break

        start_at += max_results

    if options.json_output:
        print(json.dumps(sprints, indent=4, sort_keys=False))
    else:

        def __fmt_opt(val):
            return "" if val is None else str(val)

        print(tabulate.tabulate(
            [(s["id"], s["name"], s["state"], __fmt_opt(s["start_date"]), __fmt_opt(s["end_date"]))
             for s in sprints],
            headers=["Id", "Name", "State", "Start", "End"], tablefmt="orgtbl"))

    return 0


if __name__ == '__main__':
    sys.exit(main(parse_options(sys.argv[1:])))
