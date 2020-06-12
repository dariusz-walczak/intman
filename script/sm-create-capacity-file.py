#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line script creating sprint capacity report file"""

# Standard library imports
import datetime
import json
import sys

# Third party imports
import dateutil.parser
import jsonschema
import tabulate
import holidays

# Project imports
import cjm.cfg
import cjm.codes
import cjm.run
import cjm.schema
import cjm.sprint
import cjm.team


def parse_options(args):
    """Parse command line options"""
    defaults = cjm.cfg.load_defaults()
    parser = cjm.cfg.make_common_parser(defaults)

    default_commitment_prefix = ""  # defaults.get("project", {}).get("key")

    parser.add_argument(
        "--prefix", action="store", metavar="KEY", dest="commitment_prefix",
        default=default_commitment_prefix,
        help=(
            "Prefix to which the empty comment prefix will be changed{0:s}"
            "".format(cjm.cfg.fmt_dft(default_commitment_prefix))))

    parser.add_argument(
        "sprint_file", action="store",
        help=(
            "Path to the json sprint data file as generated by the {0:s} script and described by"
            " the {1:s} schema"
            "".format(cjm.SM_CREATE_SPRINT_FILE, cjm.schema.make_subpath("sprint.json"))))

    return parser.parse_args(args)


def main(options):
    """Entry function"""
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

    # Load team data:

    team_data = cjm.data.load(cfg, cfg["path"]["team"], "team.json")

    def __holidays_in_sprint():
        sprint_holidays = []
        sprint_start_date = dateutil.parser.parse(sprint_data["start date"]).date()
        sprint_end_date = dateutil.parser.parse(sprint_data["end date"]).date()
        sprint_start_date = sprint_start_date - datetime.timedelta(days=1)
        sprint_end_date = sprint_end_date + datetime.timedelta(days=1)

        sprint_year = range(sprint_start_date.year, sprint_end_date.year+1)

        def __is_weekend(date):
            return date.weekday() >= 5

        for date, _ in sorted(holidays.PL(years=sprint_year).items()):
            if date > sprint_start_date and date < sprint_end_date and not __is_weekend(date):
                sprint_holidays.append(date)

        return sprint_holidays

    holidays_str = [d.strftime("%Y-%m-%d") for d in __holidays_in_sprint()]

    people = team_data["people"]
    for p in team_data["people"]:
        p["personal holidays"] = []

    capacity_json = {
        "people" : people,
        "national holidays": holidays_str,
        "additional holidays": []
    }

    capacity_schema = cjm.schema.load(cfg, "capacity.json")
    jsonschema.validate(capacity_json, capacity_schema)

    if options.json_output:
        print(json.dumps(capacity_json, indent=4, sort_keys=False))
    else:
        if holidays_str:
            print(
                tabulate.tabulate(
                    [(i+1, d) for i, d in enumerate(holidays_str)],
                    headers=["Holiday date"], tablefmt="orgtbl"))
        print(
            tabulate.tabulate(
                [(p["account id"], p["first name"]+" "+p["last name"], p["daily capacity"])
                 for p in team_data["people"]],
                headers=["Account ID", "Name", "Daily capacity"], tablefmt="orgtbl"))

if __name__ == "__main__":
    cjm.run.run(main, parse_options(sys.argv[1:]))
