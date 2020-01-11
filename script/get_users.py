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

    print(json.dumps(json.loads(response.text), sort_keys=True, indent=4, separators=(",", ": ")))


def parse_options(args):
    pass


if __name__ == "__main__":
    exit(main(parse_options(argv[1:])))
