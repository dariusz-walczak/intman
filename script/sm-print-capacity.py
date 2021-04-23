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
import cjm.data
import cjm.run
import cjm.schema
import cjm.codes
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
    team_capacity = cjm.capacity.process_team_capacity(sprint_data, capacity_data)

    people = sorted(
        [cjm.capacity.process_person_capacity(team_capacity, p) for p in capacity_data["people"]],
        key=lambda p: (p["last name"], p["first name"]))

    print(
        tabulate.tabulate(
            [[p["last name"], p["first name"], p["daily capacity"], p["sprint workday count"],
              p["sprint capacity"]] for p in people],
            headers=["Last Name", "First Name", "Daily Cap.", "Workdays", "Sprint Cap."],
            tablefmt="orgtbl"))

if __name__ == "__main__":
    cjm.run.run(main, parse_options(sys.argv[1:]))
