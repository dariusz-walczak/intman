#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line script pushing task list into jira"""

# Standard library imports
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

    return parser.parse_args(args)


def main(options):
    """Entry function"""
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)

    tasks_json = {
        "set id": secrets.token_hex(16),
        "author": cfg["jira"]["user"]["name"],
        "date": datetime.date.today().isoformat(),
        "tasks": []
    }

    tasks_schema = cjm.schema.load(cfg, "tasks.json")
    jsonschema.validate(tasks_json, tasks_schema)

    print(json.dumps(tasks_json, indent=4, sort_keys=False))

    return cjm.codes.NO_ERROR


if __name__ == '__main__':
    cjm.run.run(main, parse_options(sys.argv[1:]))
