# Standard library imports
import argparse
import copy
import os.path
import sys
import json


DEFAULT_FILE = ".cjm.json"

USER_NAME_ARG_NAME = "--user"
USER_TOKEN_ARG_NAME = "--token"


def init_defaults():
    return {
        "jira": {
            "scheme": "https",
            "host":   "openness.atlassian.net",
            "user": {
                "name": None,
                "token": None
            },
            "fields": {
                "story points": None
            }
        },
        "sprint": {
            "id": None
        },
        "board": {
            "id": None
        },
        "issue": {
            "include unassigned": False
        },
        "client": {
            "name": None
        },
        "project": {
            "key": None
        },
        "path": {
            "data": None,
            "output": None
        }
    }


def load_defaults(file_name=DEFAULT_FILE):
    if os.path.exists(file_name):
        try:
            with open(file_name) as defaults_file:
                defaults = json.load(defaults_file)
        except IOError as e:
            sys.stderr.write(
                "WARNING: Defaults file ('{0:s}') I/O error\n".format(file_name))
            sys.stderr.write("    {0:s}\n".format(e))
            defaults = {}
    else:
        defaults = {}

    return defaults


def apply_options(cfg, options):
    cfg = copy.copy(cfg)
    cfg["jira"]["user"]["name"] = options.user_name
    cfg["jira"]["user"]["token"] = options.user_token
    cfg["path"]["data"] = options.data_dir_path
    return cfg


def fmt_dft(v):
    return "" if v is None else " (default: {0})".format(v)


def make_common_parser(defaults):
    default_data_path = os.path.relpath(
        os.path.join(
            os.path.realpath(__file__),
            "..", "..", "..", "data"))
    default_user_name = defaults.get("jira", {}).get("user", {}).get("name", None)
    default_user_token = defaults.get("jira", {}).get("user", {}).get("token", None)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        USER_NAME_ARG_NAME, action="store", metavar="NAME", dest="user_name",
        default=default_user_name,
        help=(
            "User NAME to be used to access the cloud Jira API{0:s}"
            "".format(fmt_dft(default_user_name))))
    parser.add_argument(
        USER_TOKEN_ARG_NAME, action="store", metavar="VALUE", dest="user_token",
        default=default_user_token,
        help=(
            "User token to be used to access the cloud Jira API{0:s}"
            "".format(fmt_dft(default_user_token))))
    parser.add_argument(
        "--json-output", action="store_true", dest="json_output",
        help="Print the results serialized to JSON")
    parser.add_argument(
        "--data-dir", action="store", metavar="PATH", dest="data_dir_path",
        default=default_data_path,
        help="Toolchain data directory PATH (default: '{0:s}')".format(default_data_path))
    parser.add_argument(
        "--verbose", action="store_true", dest="verbose",
        help="Provide verbose diagnostic information")

    return parser
