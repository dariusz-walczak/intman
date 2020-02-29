#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Standard library imports
import sys
import json
import dateutil.parser
import datetime

# Third party imports
import jsonschema
import tabulate
import holidays

# Project imports
import cjm.cfg
import cjm.schema
import cjm.codes
import cjm.sprint
import cjm.team

_COMMITMENT_PREFIX_ARG_NAME = "--prefix"

def parse_options(args):
    defaults = cjm.cfg.load_defaults()
    parser = cjm.cfg.make_common_parser(defaults)

    default_commitment_prefix = ""  # defaults.get("project", {}).get("key")

    parser.add_argument(
        _COMMITMENT_PREFIX_ARG_NAME, action="store", metavar="KEY", dest="commitment_prefix",
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

    parser.add_argument(
        "team_file", action="store",
        help=(
            "Path to the json team data file as generated by the {0:s} script and described by"
            " the {1:s} schema"
            "".format(cjm.SM_CREATE_TEAM_FILE, cjm.schema.make_subpath("team.json"))))

    return parser.parse_args(args)

   
def main(options):

    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)

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
            if date > sprint_start_date and date < sprint_end_date and not __is_weekend(date) : 
                sprint_holidays.append(date) 

        return sprint_holidays 

    holidays_str = [ d.strftime("%Y-%m-%d") for d in __holidays_in_sprint()]

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
            print(tabulate.tabulate( [ (i+1,d) for i,d in enumerate(holidays_str)], headers=["Holiday date"], tablefmt="orgtbl"))
        print(tabulate.tabulate(
            [(p["account id"], p["first name"]+" "+p["last name"], p["daily capacity"]) for p in team_data["people"]],
            headers=["Account ID", "Name", "Daily capacity"], tablefmt="orgtbl"))

if __name__ == "__main__":
    exit(main(parse_options(sys.argv[1:])))