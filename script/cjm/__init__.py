# Standard library imports
import argparse
import os.path
import sys
import urllib.parse

# Third party imports
import simplejson


def fmt_dft(v):
    return "" if v is None else " (default: {0})".format(v)


def make_common_parser(defaults):
    default_user_name = defaults.get("jira", {}).get("user", {}).get("name", None)
    default_user_token = defaults.get("jira", {}).get("user", {}).get("token", None)
    default_jira_host = defaults.get("jira", {}).get("host", "openness.atlassian.net")
    default_jira_scheme = defaults.get("jira", {}).get("scheme", "https")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--user", action="store", metavar="NAME", dest="user_name", default=default_user_name,
        help=(
            "User NAME to be used to access the cloud Jira API{0:s}"
            "".format(fmt_dft(default_user_name))))
    parser.add_argument(
        "--token", action="store", metavar="VALUE", dest="user_token", default=default_user_token,
        help=(
            "User token to be used to access the cloud Jira API{0:s}"
            "".format(fmt_dft(default_user_token))))
    parser.add_argument(
        "--json-output", action="store_true", dest="json_output",
        help="Print the results serialized to JSON")

    return parser


_CJ_API_PATH = "rest/api/3"
_CJ_AGILE_PATH = "rest/agile/1.0"

DEFAULTS_FILE_NAME = ".cjm.json"


def load_defaults(file_name=DEFAULTS_FILE_NAME):
    if os.path.exists(DEFAULTS_FILE_NAME):
        try:
            with open(DEFAULTS_FILE_NAME) as defaults_file:
                defaults = simplejson.load(defaults_file)
        except IOError as e:
            sys.stderr.write(
                "WARNING: Defaults file ('{0:s}') I/O error\n".format(DEFAULTS_FILE_NAME))
            sys.stderr.write("    {0:s}\n".format(e))
            defaults = {}
    else:
        defaults = {}

    return defaults


def make_cj_url(cfg, resource_path):
    url_parts = (
        cfg["jira"]["scheme"], cfg["jira"]["host"], "/".join((_CJ_API_PATH, resource_path)),
        "", "", "")
    return urllib.parse.urlunparse(url_parts)


def make_cj_agile_url(cfg, resource_path):
    url_parts = (
        cfg["jira"]["scheme"], cfg["jira"]["host"], "/".join((_CJ_AGILE_PATH, resource_path)),
        "", "", "")
    return urllib.parse.urlunparse(url_parts)
