#!/usr/bin/env python3
from sys import argv

import requests
from requests.auth import HTTPBasicAuth
import json
import argparse


def main(options):
    out_file = "../data/team_data.json"
    pretty_out_file = "../data/team_data_pretty.json"

    url = "https://openness.atlassian.net/rest/api/3/users"

    auth = HTTPBasicAuth("email@example.com", "<api_token>")

    headers = {
        "Accept": "application/json"
    }

    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth
    )

    all_users_data = json.loads(response.text)
    human_users = [user for user in all_users_data if user["accountType"] == "atlassian"]

    users = list()
    for user in human_users:
        if str(user["displayName"]).find(' ') != -1:
            firstname, lastname = str(user["displayName"]).split(" ", 1)
        elif str(user["displayName"]).find('.') != -1:
            firstname, lastname = str(user["displayName"]).split(".", 1)
        elif str(user["displayName"]).find(',') != -1:
            firstname, lastname = str(user["displayName"]).split(",", 1)
        else:
            firstname = user["displayName"]
            lastname = "LASTNAME"

        acc_id = user["accountId"]
        acc_id_last_3_digs = "".join(list(acc_id)[-3:])
        code = str(firstname[0] + lastname[0] + "." + acc_id_last_3_digs).upper()

        # username and userKey is deprecated and replaced by accountId
        # https://developer.atlassian.com/cloud/jira/platform/deprecation-notice-user-privacy-api-migration-guide/
        users.append({"code": code, "last name": lastname, "first name": firstname, "account ID": acc_id})

    people = dict()
    people.update({"people": users})

    people_json = json.loads(json.dumps(people))

    try:
        with open(out_file, "w") as file_object:
            json.dump(people_json, file_object)
            print(f"{out_file} created.")
    except FileNotFoundError:
        print(f"Error writing file {out_file}.")

    try:
        with open(pretty_out_file, "w") as pretty_file_object:
            json.dump(people_json, pretty_file_object, indent=4, separators=(',', ': '))
            print(f"{pretty_out_file} created.")
    except FileNotFoundError:
        print(f"Error writing file {pretty_out_file}.")

    return 0


def parse_options(args):
    pass


if __name__ == "__main__":
    exit(main(parse_options(argv[1:])))
