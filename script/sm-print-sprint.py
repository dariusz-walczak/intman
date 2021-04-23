#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: MIT
# Copyright (C) 2020-2021 Mobica Limited

# Standard library imports
import sys
import datetime

# Third party imports
import holidays
import jsonschema
import numpy
import tabulate

# Project imports
import cjm.capacity
import cjm.cfg
import cjm.codes
import cjm.data
import cjm.run
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

    return parser.parse_args(args)

   
def main(options):
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)

    # Load sprint data:

    sprint_data = cjm.data.load(cfg, options.sprint_file, "sprint.json")

    # Load other data:

    print(tabulate.tabulate(
        [(key, sprint_data[key])
         for key in ["start date", "end date", "name", "id", "comment prefix"]] +
        [("project/{0:s}".format(key), sprint_data["project"][key]) for key in ["key", "name"]],
        tablefmt="orgtbl"))

    return cjm.codes.NO_ERROR
#       tabulate.tabulate(
#            [[p["last name"], p["first name"], p["daily capacity"], p["sprint workday count"],
#              p["sprint capacity"]] for p in people],
#            headers=["Last Name", "First Name", "Daily Cap.", "Workdays", "Sprint Cap."],
#            tablefmt="orgtbl"))



if __name__ == "__main__":
    cjm.run.run(main, parse_options(sys.argv[1:]))
