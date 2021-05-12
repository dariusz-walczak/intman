#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# SPDX-License-Identifier: MIT
# Copyright (C) 2020-2021 Mobica Limited

"""Create team file basing on specified project members"""

# Standard library imports
import sys
import json

# Third party imports
import jsonschema

# Project imports
import cjm
import cjm.cfg
import cjm.codes
import cjm.request
import cjm.run
import cjm.schema

_PROJECT_KEY_ARG_NAME = "--project-key"
_DEFAULT_DAILY_CAPACITY = 2

def request_users(cfg):
    """Retrieve list of project members"""
    users = []

    user_data_url = cjm.request.make_cj_url(cfg, "user", "search", "query")
    user_query = "is assignee of {0:s}".format(cfg["project"]["key"])

    start_at = 0
    max_results = 50

    while True:
        response = cjm.request.make_cj_request(
            cfg, user_data_url,
            {"query": user_query, "startAt": start_at, "maxResults": max_results})
        response_json = response.json()
        users += response_json["values"]
        start_at += max_results

        if start_at >= response_json["total"]:
            break

    return users


def main(options, defaults):
    """Entry function"""
    cfg = cjm.cfg.apply_options(cjm.cfg.apply_config(cjm.cfg.init_defaults(), defaults), options)
    cfg["project"]["key"] = options.project_key

    if cfg["project"]["key"] is None:
        sys.stderr.write(
            "ERROR: The project key is not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it".format(_PROJECT_KEY_ARG_NAME))
        return cjm.codes.CONFIGURATION_ERROR

    users_active = [u for u in request_users(cfg) if u["active"]]
    users = []

    for user in users_active:
        if str(user["displayName"]).find(' ') != -1:
            firstname, lastname = str(user["displayName"]).split(" ", 1)
        elif str(user["displayName"]).find('.') != -1:
            firstname, lastname = str(user["displayName"]).split(".", 1)
        elif str(user["displayName"]).find(',') != -1:
            firstname, lastname = str(user["displayName"]).split(",", 1)
        else:
            firstname = user["displayName"]
            lastname = "PLEASE-FILL"

        data = {
            "code": str(firstname[0] + lastname[0]).upper(),
            "last name": lastname,
            "first name": firstname,
            "account id": user["accountId"],
            "daily capacity": options.daily_capacity
        }
        users.append(data)

    make_codes_unique(users)

    people = {"people": users}

    print(json.dumps(people, indent=4, separators=(',', ': ')))

    jsonschema.validate(people, cjm.schema.load(cfg, "team.json"))

    if options.json_output:
        print(json.dumps(people, indent=4, sort_keys=False))

    return cjm.codes.NO_ERROR


def make_codes_unique(users):
    """Ensure that user codes are unique by adding unique index postfix to all the duplicates"""

    codes = [user["code"] for user in users]
    unique_codes = []

    for idx, code in enumerate(codes):
        total = codes.count(code)
        count = codes[:idx].count(code)
        unique_codes.append("{0:s}{1:d}".format(code, count + 1) if total > 1 else code)

    for idx, user in enumerate(users):
        user["code"] = unique_codes[idx]


def parse_options(args, defaults):
    """Parse command line options"""
    parser = cjm.cfg.make_common_parser(defaults)

    default_project_key = defaults.get("project", {}).get("key")

    parser.add_argument(
        _PROJECT_KEY_ARG_NAME, action="store", metavar="KEY", dest="project_key",
        default=default_project_key,
        help=(
            "Project for which the team will be associated{0:s}"
            "".format(cjm.cfg.fmt_dft(default_project_key))))

    parser.add_argument(
        "--daily_capacity", action="store", default=_DEFAULT_DAILY_CAPACITY,
        dest="daily_capacity",
        help=("Change default daily capacity for every team member"
              f"current default: {_DEFAULT_DAILY_CAPACITY }"))

    return parser.parse_args(args)


if __name__ == "__main__":
    cjm.run.run_2(main, parse_options)
