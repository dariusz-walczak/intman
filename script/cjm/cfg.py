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

CALENDAR_WEEK_SYSTEM_NORTH_AMERICAN = "North American"
CALENDAR_WEEK_SYSTEM_ISO = "ISO"


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
                "story points": None,
                "epic link": None,
                "epic name": None
            },
            "issue": {
                "type": {
                    "epic": None,
                    "task": None
                }
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
            "key": None,
            "code": None,
            "sow": None,
            "id": None
        },
        "calendar": {
            "week": {
                "system": None, # Week numbering system (CALENDAR_WEEK_SYSTEM_ISO or
                                #  CALENDAR_WEEK_SYSTEM_NORTH_AMERICAN)
                "name": {
                    "lower offset": 0, # Number of days to be added to the sprint start date (may
                                       #  be negative) to determine sprint start week name
                                       #  (affects starting weeks split between years)
                    "upper offset": 0  # Number of days to be added to the sprint end date to (may
                                       #  be negative) to determine sprint end week name (affects
                                       #  ending weeks split between years)
                }
            }
        },
        "report": {
            "capacity": {
                "page break": {
                    "absence section": True,
                    "weekly table": False
                }
            }
        },
        "path": {
            "data": None,
            "output": None,
            "team": None,
            "capacity": None,
            "commitment": None,
            "delivery": None
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
    cfg["path"]["team"] = options.team_file_path
    cfg["path"]["capacity"] = options.capacity_file_path
    cfg["path"]["commitment"] = options.commitment_file_path
    cfg["path"]["delivery"] = options.delivery_file_path
    cfg["calendar"]["week"]["system"] = options.week_numbering_system
    return cfg


def apply_config(cfg, defaults):
    """
    Apply selected defaults file entries directly to the config data structure. These specific
    parameters can't typically be overridden by the command-line options
    """
    cfg = copy.copy(cfg)
    pb_config = defaults.get("report", {}).get("capacity", {}).get("page break", {})
    cfg["report"]["capacity"]["page break"]["absence section"] = pb_config.get(
        "absence section", cfg["report"]["capacity"]["page break"]["absence section"])
    cfg["report"]["capacity"]["page break"]["weekly table"] = pb_config.get(
        "weekly table", cfg["report"]["capacity"]["page break"]["weekly table"])

    wn_config = defaults.get("calendar", {}).get("week", {}).get("name", {})
    cfg["calendar"]["week"]["name"]["lower offset"] = wn_config.get(
        "lower offset", cfg["calendar"]["week"]["name"]["lower offset"])
    cfg["calendar"]["week"]["name"]["upper offset"] = wn_config.get(
        "upper offset", cfg["calendar"]["week"]["name"]["upper offset"])

    return cfg


def fmt_dft(val):
    """Generate default argument description

    This secondary utility function is supporting formatting of command line argument help string
    """
    return "" if val is None else " (default: {0})".format(val)


def fmt_dft_token(val):
    """Generate obfuscated default token argument description

    This secondary utility function is supporting formatting of command line argument help string
    """
    if val is None:
        return ""

    token_len = len(val)
    char_cnt = max(int((token_len-4)/6), 0)
    token = "{0:s}{1:s}{2:s}".format(
        val[:char_cnt], "*"*(token_len-char_cnt*2), val[token_len-char_cnt:])

    return " (default: {0})".format(token)


def make_common_parser(defaults):
    """Create a new command line argument parser (using argparse module) and populate it with
    common options

    In case of most applications the returned parser object will be extended by application
    specific arguments"""
    default_data_path = os.path.relpath(
        os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            "..", "..", "data"))
    default_user_name = defaults.get("jira", {}).get("user", {}).get("name")
    default_user_token = defaults.get("jira", {}).get("user", {}).get("token")
    default_host_name = defaults.get("jira", {}).get("host")
    default_scheme = defaults.get("jira", {}).get("scheme")
    default_wns = defaults.get("calendar", {}).get("week", {}).get(
        "system", CALENDAR_WEEK_SYSTEM_ISO)

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
            "".format(fmt_dft_token(default_user_token))))
    parser.add_argument(
        "--json-output", action="store_true", dest="json_output",
        help="Print the results serialized to JSON")
    parser.add_argument(
        "--data-dir", action="store", metavar="PATH", dest="data_dir_path",
        default=default_data_path,
        help="Toolchain data directory PATH (default: '{0:s}')".format(default_data_path))
    parser.add_argument(
        "--team-file", action="store", metavar="PATH", dest="team_file_path",
        help="Override of the default team data file associated with given sprint")
    parser.add_argument(
        "--capacity-file", action="store", metavar="PATH", dest="capacity_file_path",
        help="Override of the default capacity data file associated with given sprint")
    parser.add_argument(
        "--commitment-file", action="store", metavar="PATH", dest="commitment_file_path",
        help="Override of the default commitment data file associated with given sprint")
    parser.add_argument(
        "--delivery-file", action="store", metavar="PATH", dest="delivery_file_path",
        help="Override of the default delivery data file associated with given sprint")
    parser.add_argument(
        "--week-system", action="store", metavar="SYSTEM",
        choices=(CALENDAR_WEEK_SYSTEM_ISO, CALENDAR_WEEK_SYSTEM_NORTH_AMERICAN),
        dest="week_numbering_system", default=default_wns,
        help=(
            "Week numbering system ('{0:s}' or '{1:s}', default: '{2:s}')".format(
                CALENDAR_WEEK_SYSTEM_NORTH_AMERICAN, CALENDAR_WEEK_SYSTEM_ISO,
                default_wns)))
    parser.add_argument(
        "--verbose", action="store_true", dest="verbose",
        help="Provide verbose diagnostic information")

    return parser
