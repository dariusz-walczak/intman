#!/usr/bin/env python3
from sys import argv

import requests
from requests.auth import HTTPBasicAuth
import json
import argparse


def main(options):
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

    people = list()
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

        acc_id_last_3_digs = "".join(list(user["accountId"])[-3:])
        code = str(firstname[0] + lastname[0] + "." + acc_id_last_3_digs).upper()

        people.append({"code": code, "first name": firstname, "last name": lastname})

    print(json.dumps(people, sort_keys=True, indent=4, separators=(",", ": ")))


def parse_options(args):
    pass


if __name__ == "__main__":
    exit(main(parse_options(argv[1:])))
