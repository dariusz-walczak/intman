# Standard library imports
import argparse
import os.path
import sys
import urllib.parse

# Third party imports
import requests
import simplejson


USER_NAME_ARG_NAME = "--user"
USER_TOKEN_ARG_NAME = "--token"

def fmt_dft(v):
    return "" if v is None else " (default: {0})".format(v)


def make_common_parser(defaults):
    default_data_path = os.path.relpath(
        os.path.join(
            os.path.realpath(__file__),
            "..", "..", "..", "data"))
    default_user_name = defaults.get("jira", {}).get("user", {}).get("name", None)
    default_user_token = defaults.get("jira", {}).get("user", {}).get("token", None)
    default_jira_host = defaults.get("jira", {}).get("host", "openness.atlassian.net")
    default_jira_scheme = defaults.get("jira", {}).get("scheme", "https")

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


def make_cj_url(cfg, *resource_path):
    url_parts = (
        cfg["jira"]["scheme"], cfg["jira"]["host"], "/".join((_CJ_API_PATH, *resource_path)),
        "", "", "")
    return urllib.parse.urlunparse(url_parts)


def make_cj_agile_url(cfg, *resource_path):
    url_parts = (
        cfg["jira"]["scheme"], cfg["jira"]["host"], "/".join((_CJ_AGILE_PATH, *resource_path)),
        "", "", "")
    return urllib.parse.urlunparse(url_parts)


def make_cj_request(cfg, url):
    if cfg["jira"]["user"]["name"] is None:
        sys.stderr.write(
            "ERROR: Jira user name not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(USER_NAME_ARG_NAME))
        return (1, None)

    if cfg["jira"]["user"]["token"] is None:
        sys.stderr.write(
            "ERROR: Jira user token not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(USER_TOKEN_ARG_NAME))
        return (1, None)

    response = requests.get(
        url, auth=(cfg["jira"]["user"]["name"], cfg["jira"]["user"]["token"]))

    if response.status_code != 200:
        sys.stderr.write(
            "ERROR: The Jira API request ('{0:s}') failed with code {1:d}\n"
            "".format(url, response.status_code))
        return (2, response)

    return (0, response)


def schema_load(cfg, name):
    schema_path = os.path.join(cfg["path"]["data"], "cjm", "schema", name)
    return simplejson.load(open(schema_path))
