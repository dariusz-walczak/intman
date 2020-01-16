#!/usr/bin/env python3

# Standard library imports
import sys

import jsonschema
import requests
from requests.auth import HTTPBasicAuth
import json

# Project imports
import cjm
import cjm.cfg
import cjm.request
import cjm.codes
import cjm.schema

_PROJECT_KEY_ARG_NAME = "--project-key"


def main(options):
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)
    cfg["project"]["key"] = options.project_key

    if cfg["project"]["key"] is None:
        sys.stderr.write(
            "ERROR: The project key is not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it".format(_PROJECT_KEY_ARG_NAME))
        return cjm.codes.CONFIGURATION_ERROR

    project_data_url = cjm.request.make_cj_url(cfg, "users")
    result_code, response = cjm.request.make_cj_request(cfg, project_data_url)

    if result_code:
        return result_code

    raw_json = response.json()
    human_users = [user for user in raw_json if user["accountType"] == "atlassian"]

    users = []

    for user in human_users:
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

        data = {
            "code": code,
            "last name": lastname,
            "first name": firstname,
            "user name": "",
            "account id": acc_id
        }

        # username and userKey is deprecated and replaced by accountId
        # https://developer.atlassian.com/cloud/jira/platform/deprecation-notice-user-privacy-api-migration-guide/
        users.append(data)

    codes = [user["code"] for user in users]
    unique_codes = []

    for idx, user in enumerate(codes):
        total = codes.count(user)
        count = codes[:idx].count(user)
        unique_codes.append(user + str(count + 1) if total > 1 else user)

    for idx, user in enumerate(users):
        user["code"] = unique_codes[idx]

    people = {"people": users}

    people_json = json.loads(json.dumps(people))
    print(json.dumps(people_json, indent=4, separators=(',', ': ')))

    # team = {
    #     "people": [
    #         {
    #             "code": ,
    #             "last name": ,
    #             "first name": ,
    #             "user name": ,
    #             "account id":
    #         }
    # }
    #
    # team_schema = cjm.schema.load(cfg, "team.json")
    # jsonschema.validate(sprint, team_schema)

    return cjm.codes.NO_ERROR


def parse_options(args):
    defaults = cjm.cfg.load_defaults()
    parser = cjm.cfg.make_common_parser(defaults)

    default_project_key = defaults.get("project", {}).get("key")

    parser.add_argument(
        _PROJECT_KEY_ARG_NAME, action="store", metavar="KEY", dest="project_key",
        default=default_project_key,
        help=(
            "Project with which the sprint will be associated{0:s}"
            "".format(cjm.cfg.fmt_dft(default_project_key))))

    return parser.parse_args(args)


if __name__ == "__main__":
    sys.stderr.write("TODO: ADD ADDITIONAL ARGUMENTS TO PARSING\n")
    sys.stderr.write("TODO: JSON SCHEMA VALIDATE\n")
    exit(main(parse_options(sys.argv[1:])))
