#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Command line script listing all available Jira projects"""

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


def parse_options(args):
    """Parse command line options"""
    defaults = cjm.cfg.load_defaults()
    parser = cjm.cfg.make_common_parser(defaults)

    return parser.parse_args(args)


def main(options):
    """Entry function"""
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)

    response = requests.get(
        cjm.request.make_cj_url(cfg, "project/search"),
        auth=(cfg["jira"]["user"]["name"], cfg["jira"]["user"]["token"])
    )

    projects = []

    for project in response.json()["values"]:
        project_data = {
            "id":   project["id"],
            "key":  project["key"],
            "name": project["name"]
        }
        projects.append(project_data)

    if options.json_output:
        print(json.dumps(projects, indent=4, sort_keys=False))
    else:
        print(tabulate.tabulate(
            [(p["id"], p["key"], p["name"]) for p in projects],
            headers=["Id", "Key", "Name"], tablefmt="orgtbl"))

    return 0


if __name__ == '__main__':
    sys.exit(main(parse_options(sys.argv[1:])))
