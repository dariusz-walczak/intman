#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: MIT
# Copyright (C) 2020-2021 Mobica Limited

"""Command line script listing boards"""

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
    """Parse command line options"""
    defaults = cjm.cfg.load_defaults()
    parser = cjm.cfg.make_common_parser(defaults)

    default_project_key = defaults.get("project", {}).get("key")

    parser.add_argument(
        "--project-key", action="store", metavar="KEY", dest="project_key",
        default=default_project_key,
        help=(
            "Project to list the boards for{0:s}"
            "".format(cjm.cfg.fmt_dft(default_project_key))))
    parser.add_argument(
        "--all", action="store_true", dest="all_boards",
        help="List boards for all projects (overrides --project-key)")

    return parser.parse_args(args)


def main(options):
    """Entry function"""
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)
    cfg["project"]["key"] = options.project_key

    response = requests.get(
        cjm.request.make_cj_agile_url(cfg, "board"),
        auth=(cfg["jira"]["user"]["name"], cfg["jira"]["user"]["token"])
    )

    boards = []

    for board in response.json()["values"]:
        project_key = cfg["project"]["key"]
        board_project_key = board.get("location", {}).get("projectKey")

        if ((project_key is None) or options.all_boards or
                (board_project_key is not None and project_key == board_project_key)):
            board_data = {
                "id": board["id"],
                "name": board["name"]
            }
            boards.append(board_data)

    if options.json_output:
        print(json.dumps(boards, indent=4, sort_keys=False))
    else:
        print(tabulate.tabulate(
            [(b["id"], b["name"]) for b in boards],
            headers=["Id", "Name"], tablefmt="orgtbl"))

    return 0


if __name__ == '__main__':
    sys.exit(main(parse_options(sys.argv[1:])))
