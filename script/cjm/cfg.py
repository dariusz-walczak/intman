"""Support configurability of cjm applications"""

# Standard library imports
import argparse
import copy
import os.path
import sys
import json


DEFAULT_FILE = ".cjm.json"

HOST_NAME_ARG_NAME = "--host"
SCHEME_ARG_NAME = "--scheme"
USER_NAME_ARG_NAME = "--user"
USER_TOKEN_ARG_NAME = "--token"


def init_defaults():
    """Init invocation context data tree

    The purpose of the invocation context data tree is to simplify propagation of multiple
    common function invocation parameters

    This function should actually be named init_context
    """
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
            "include unassigned": False,
            "allow late delivery": False
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
    """Load command line arguments defaults from given file name"""

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
    """Apply command line options parsed by the make_common_parser function to the context data
    tree created by the init_defaults function"""
    cfg = copy.copy(cfg)
    cfg["jira"]["host"] = options.host_name
    cfg["jira"]["scheme"] = options.scheme
    cfg["jira"]["user"]["name"] = options.user_name
    cfg["jira"]["user"]["token"] = options.user_token
    cfg["path"]["data"] = options.data_dir_path
    return cfg


def fmt_dft(val):
    """Generate default argument description

    This secondary utility function is supporting formatting of command line argument help string
    """
    return "" if val is None else " (default: {0})".format(val)


def make_common_parser(defaults):
    """Create a new command line argument parser (using argparse module) and populate it with
    common options

    In case of most applications the returned parser object will be extended by application
    specific arguments"""
    default_data_path = os.path.relpath(
        os.path.join(
            os.path.realpath(__file__),
            "..", "..", "..", "data"))
    default_user_name = defaults.get("jira", {}).get("user", {}).get("name")
    default_user_token = defaults.get("jira", {}).get("user", {}).get("token")
    default_host_name = defaults.get("jira", {}).get("host")
    default_scheme = defaults.get("jira", {}).get("scheme")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        SCHEME_ARG_NAME, action="store", metavar="NAME", dest="scheme",
        default=default_scheme,
        help=(
            "URL scheme to be used to access the cloud Jira API{0:s}"
            "".format(fmt_dft(default_scheme))))
    parser.add_argument(
        HOST_NAME_ARG_NAME, action="store", metavar="NAME", dest="host_name",
        default=default_host_name,
        help=(
            "Host NAME to be used to access the cloud Jira API{0:s}"
            "".format(fmt_dft(default_host_name))))
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
