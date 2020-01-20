#!/usr/bin/env python3

# Standard library imports
import datetime
import json
import os.path
import sys

# Third party imports
import jsonschema
import requests
import simplejson
import tabulate

# Project imports
import cjm
import cjm.cfg
import cjm.request
import cjm.schema
import cjm.sprint
import cjm.codes


_PROJECT_KEY_ARG_NAME = "--project-key"

def parse_options(args):
    defaults = cjm.cfg.load_defaults()
    parser = cjm.cfg.make_common_parser(defaults)

    default_length = 14
    default_project_key = defaults.get("project", {}).get("key")

    start_flags = parser.add_mutually_exclusive_group()
    start_flags.add_argument(
        "--next-week", action="store_true", dest="next_week_flag",
        help=(
            "The first day of the sprint is the next week's Monday. This option is the default"
            " if none of sprint start options is given"))
    start_flags.add_argument(
        "--this-week", action="store_true", dest="this_week_flag",
        help="The first day of the sprint is this week's Monday")
    start_flags.add_argument(
        "--last-week", action="store_true", dest="last_week_flag",
        help="The first day of the sprint is the last week's Monday")
    start_flags.add_argument(
        "--start", action="store", metavar="DATE", dest="start_date",
        type=lambda d: datetime.datetime.strptime(d, '%Y-%m-%d').date(),
        help="The first day of the sprint is the DATE (yyyy-mm-dd)")
    parser.add_argument(
        "--length", action="store", metavar="DAYS", dest="length", type=int,
        default=default_length,
        help="The sprint length in DAYS (default: {0:d})".format(default_length))

    parser.add_argument(
        _PROJECT_KEY_ARG_NAME, action="store", metavar="KEY", dest="project_key",
        default=default_project_key,
        help=(
            "Project with which the sprint will be associated{0:s}"
            "".format(cjm.cfg.fmt_dft(default_project_key))))

    return parser.parse_args(args)


def determine_start_date(options):
    if options.start_date is not None:
        return options.start_date
    else:
        today = datetime.date.today()
        week_offset = 7 if options.last_week_flag else 0 if options.this_week_flag else -7
        return today - datetime.timedelta(days=today.weekday()+week_offset)


def main(options):
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)
    cfg["project"]["key"] = options.project_key

    if cfg["project"]["key"] is None:
        sys.stderr.write(
            "ERROR: The project key is not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it".format(_PROJECT_KEY_ARG_NAME))
        return cjm.codes.CONFIGURATION_ERROR

    project_data_url = cjm.request.make_cj_url(cfg, "project", cfg["project"]["key"])
    result_code, response = cjm.request.make_cj_request(cfg, project_data_url)

    if result_code:
        return result_code

    project_json = response.json()

    start_date = determine_start_date(options)
    end_date = start_date + datetime.timedelta(days=options.length-1)
    sprint = {
        "start date": start_date.isoformat(),
        "end date": end_date.isoformat(),
        "name": cjm.sprint.generate_sprint_name(project_json["name"], start_date, end_date),
        "id": int(project_json["id"]),
        "comment prefix": "",
        "project": {
            "key": cfg["project"]["key"],
            "name": project_json["name"]
        }
    }

    sprint_schema = cjm.schema.load(cfg, "sprint.json")
    jsonschema.validate(sprint, sprint_schema)

    if options.json_output:
        print(simplejson.dumps(sprint, indent=4, sort_keys=False))
    else:
        print(tabulate.tabulate(
            [(key, sprint[key]) for key in ["start date", "end date", "name"]] +
            [("project/{0:s}".format(key), sprint["project"][key]) for key in ["key", "name"]],
            tablefmt="orgtbl"))

    return cjm.codes.NO_ERROR


if __name__ == '__main__':
    sys.exit(main(parse_options(sys.argv[1:])))
