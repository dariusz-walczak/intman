#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line script pushing task list into jira"""

# Standard library imports
import csv
import datetime
import json
import secrets
import sys

# Third party imports
import jsonschema

# Project imports
import cjm.cfg
import cjm.run
import cjm.schema


def parse_options(args):
    """Parse command line options"""
    defaults = cjm.cfg.load_defaults()
    parser = cjm.cfg.make_common_parser(defaults)

    parser.add_argument(
        "tasks_file", action="store",
        help="Path to a CSV task definition list to be converted to the JSON format")

    return parser.parse_args(args)


def load_tasks(cfg, file_name):
    """Load tasks from given CSV tasks file"""
    try:
        with open(file_name) as data_file:
            dialect = csv.Sniffer().sniff(data_file.read(1024))
            data_file.seek(0)
            reader = csv.DictReader(data_file, dialect=dialect)
            return [row for row in reader]
    except IOError as e:
        sys.stderr.write("ERROR: CSV tasks data file ('{0:s}') I/O error\n".format(file_name))
        sys.stderr.write("    {0}\n".format(e))
        raise cjm.codes.CjmError(cjm.codes.FILESYSTEM_ERROR)


def _get_required_field(idx, row, field_name):
    try:
        val = row[field_name]
    except KeyError:
        sys.stderr.write(
            "ERROR: The CSV data is missing a required '{0:s}' column\n"
            "".format(field_name))
        raise cjm.codes.CjmError(cjm.codes.INPUT_DATA_ERROR)

    if val is None or val == "":
        sys.stderr.write(
            "ERROR: Row #{0:d}: The '{1:s}' field is empty".format(idx, field_name))
        raise cjm.codes.CjmError(cjm.codes.INPUT_DATA_ERROR)

    return val


def main(options):
    """Entry function"""
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)

    tasks_raw = load_tasks(cfg, options.tasks_file)

    def __adapt_task(idx, row):
        return {
            "title": _get_required_field(idx, row, "title"),
            "summary": "-",
            "idx": idx,
            "story points": None
        }

    tasks_json = {
        "set id": secrets.token_hex(16),
        "author": cfg["jira"]["user"]["name"],
        "date": datetime.date.today().isoformat(),
        "tasks": [__adapt_task(idx, row) for idx, row in enumerate(tasks_raw, 1)]
    }

    tasks_schema = cjm.schema.load(cfg, "tasks.json")
    jsonschema.validate(tasks_json, tasks_schema)

    print(json.dumps(tasks_json, indent=4, sort_keys=False))

    return cjm.codes.NO_ERROR


if __name__ == '__main__':
    cjm.run.run(main, parse_options(sys.argv[1:]))
