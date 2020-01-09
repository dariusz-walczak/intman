#!/usr/bin/env python3

# Standard library imports
import os.path
import sys

# Third party imports
import requests
import simplejson
import tabulate

# Project imports
import cjm
import cjm.cfg


DEFAULTS_FILE_NAME = ".cjm.json"


def parse_options(args):
    defaults = cjm.load_defaults()
    parser = cjm.make_common_parser(defaults)

    return parser.parse_args(args)


def main(options):
    cfg = cjm.cfg.apply_options(cjm.cfg.init_default(), options)

    response = requests.get(
        cjm.make_cj_url(cfg, "project/search"),
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
        print(simplejson.dumps(projects, indent=4, sort_keys=False))
    else:
        print(tabulate.tabulate(
            [(p["id"], p["key"], p["name"]) for p in projects],
            headers=["Id", "Key", "Name"], tablefmt="orgtbl"))

    return 0


if __name__ == '__main__':
    sys.exit(main(parse_options(sys.argv[1:])))
