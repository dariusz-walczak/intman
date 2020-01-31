#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Standard library imports
import sys
import json

# Third party imports
import jsonschema

# Project imports
import cjm
import cjm.cfg
import cjm.request
import cjm.codes
import cjm.schema

_PROJECT_KEY_ARG_NAME = "--project-key"


def request_users(cfg):
    users = []

    user_data_url = cjm.request.make_cj_url(cfg, "user", "search", "query")
    user_query = "is assignee of {0:s}".format(cfg["project"]["key"])

    start_at = 0
    max_results = 50

    while True:
        result_code, response = cjm.request.make_cj_request(
            cfg, user_data_url,
            {"query": user_query, "startAt": start_at, "maxResults": max_results})

        if result_code:
            return result_code

        response_json = response.json()
        users += response_json["values"]
        start_at += max_results

        if start_at >= response_json["total"]:
            break

    return cjm.codes.NO_ERROR, users


def main(options):
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)
    cfg["project"]["key"] = options.project_key

    if cfg["project"]["key"] is None:
        sys.stderr.write(
            "ERROR: The project key is not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it".format(_PROJECT_KEY_ARG_NAME))
        return cjm.codes.CONFIGURATION_ERROR

    result_code, users_all = request_users(cfg)

    if result_code:
        return result_code

    users_active = [u for u in users_all if u["active"]]
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

        acc_id = user["accountId"]
        code = str(firstname[0] + lastname[0]).upper()

        user_url = cjm.request.make_cj_url(cfg, f"user?accountId={acc_id}")
        result_code, response = cjm.request.make_cj_request(cfg, user_url)

        if result_code:
            return result_code

        user_json_2 = response.json()

        data = {
            "code": code,
            "last name": lastname,
            "first name": firstname,
            "user name": user_json_2["name"],
            "account id": acc_id
        }
        users.append(data)

    codes = [user["code"] for user in users]
    unique_codes = []

    for idx, code in enumerate(codes):
        total = codes.count(code)
        count = codes[:idx].count(code)
        unique_codes.append("{0:s}{1:d}".format(code, count + 1) if total > 1 else code)

    for idx, user in enumerate(users):
        user["code"] = unique_codes[idx]

    people = {"people": users}

    print(json.dumps(people, indent=4, separators=(',', ': ')))

    team_schema = cjm.schema.load(cfg, "team.json")
    jsonschema.validate(people, team_schema)

    if options.json_output:
        print(json.dumps(people, indent=4, sort_keys=False))

    return cjm.codes.NO_ERROR


def parse_options(args):
    defaults = cjm.cfg.load_defaults()
    parser = cjm.cfg.make_common_parser(defaults)

    default_project_key = defaults.get("project", {}).get("key")

    parser.add_argument(
        _PROJECT_KEY_ARG_NAME, action="store", metavar="KEY", dest="project_key",
        default=default_project_key,
        help=(
            "Project for which the team will be associated{0:s}"
            "".format(cjm.cfg.fmt_dft(default_project_key))))

    return parser.parse_args(args)


if __name__ == "__main__":
    exit(main(parse_options(sys.argv[1:])))
