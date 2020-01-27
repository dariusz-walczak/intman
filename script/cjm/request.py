# Standard library imports
import sys
import urllib.parse

# Third party imports
import requests

# Project imports
import cjm.cfg
import cjm.codes

_CJ_API_PATH = "rest/api/3"
_CJ_AGILE_PATH = "rest/agile/1.0"
_CURRENT_USER_PATH = "/rest/gadget/1.0/currentUser"


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


def make_issue_url(cfg, issue_key):
    url_parts = (
        cfg["jira"]["scheme"], cfg["jira"]["host"], "".join(issue_key),
        "", "", "")
    return urllib.parse.urlunparse(url_parts)


def make_user_url(cfg, *resource_path):
    url_parts = (
        cfg["jira"]["scheme"], cfg["jira"]["host"], "/".join((_CJ_API_PATH, *resource_path)),
        "", "", "")
    return urllib.parse.urlunparse(url_parts)


def make_current_user_url(cfg, *resource_path):
    url_parts = (
        cfg["jira"]["scheme"], cfg["jira"]["host"], "/".join((_CURRENT_USER_PATH, *resource_path)),
        "", "", "")
    return urllib.parse.urlunparse(url_parts)


def make_cj_request(cfg, url, params=None):
    params = {} if params is None else params

    if cfg["jira"]["user"]["name"] is None:
        sys.stderr.write(
            "ERROR: Jira user name not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(cjm.cfg.USER_NAME_ARG_NAME))
        return cjm.codes.CONFIGURATION_ERROR, None

    if cfg["jira"]["user"]["token"] is None:
        sys.stderr.write(
            "ERROR: Jira user token not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(cjm.cfg.USER_TOKEN_ARG_NAME))
        return cjm.codes.CONFIGURATION_ERROR, None

    response = requests.get(
        url, params=params,
        auth=(cfg["jira"]["user"]["name"], cfg["jira"]["user"]["token"]))

    if response.status_code != 200:
        sys.stderr.write(
            "ERROR: The Jira API request ('{0:s}') failed with code {1:d}\n"
            "".format(url, response.status_code))
        return cjm.codes.REQUEST_ERROR, response

    return cjm.codes.NO_ERROR, response


def make_cj_post_request(cfg, url, json):
    if cfg["jira"]["user"]["name"] is None:
        sys.stderr.write(
            "ERROR: Jira user name not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(cjm.cfg.USER_NAME_ARG_NAME))
        return cjm.codes.CONFIGURATION_ERROR, None

    if cfg["jira"]["user"]["token"] is None:
        sys.stderr.write(
            "ERROR: Jira user token not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(cjm.cfg.USER_TOKEN_ARG_NAME))
        return cjm.codes.CONFIGURATION_ERROR, None

    response = requests.post(
        url, json=json,
        auth=(cfg["jira"]["user"]["name"], cfg["jira"]["user"]["token"]))

    if response.status_code != 200:
        sys.stderr.write(
            "ERROR: The Jira API request ('{0:s}') failed with code {1:d}\n"
            "".format(url, response.status_code))
        return cjm.codes.REQUEST_ERROR, response

    return cjm.codes.NO_ERROR, response


def make_user_request(cfg, url, params=None):
    params = {} if params is None else params

    if cfg["jira"]["user"]["name"] is None:
        sys.stderr.write(
            "ERROR: Jira user name not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(cjm.cfg.USER_NAME_ARG_NAME))
        return cjm.codes.CONFIGURATION_ERROR, None

    if cfg["jira"]["user"]["token"] is None:
        sys.stderr.write(
            "ERROR: Jira user token not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(cjm.cfg.USER_TOKEN_ARG_NAME))
        return cjm.codes.CONFIGURATION_ERROR, None

    response = requests.get(
        url, params=params,
        auth=(cfg["jira"]["user"]["name"], cfg["jira"]["user"]["token"]))

    if response.status_code != 200:
        sys.stderr.write(
            "ERROR: The Jira API request ('{0:s}') failed with code {1:d}\n"
            "".format(url, response.status_code))
        return cjm.codes.REQUEST_ERROR, response

    return cjm.codes.NO_ERROR, response


def make_current_user_request(cfg, url, params=None):
    params = {} if params is None else params

    if cfg["jira"]["user"]["name"] is None:
        sys.stderr.write(
            "ERROR: Jira user name not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(cjm.cfg.USER_NAME_ARG_NAME))
        return cjm.codes.CONFIGURATION_ERROR, None

    if cfg["jira"]["user"]["token"] is None:
        sys.stderr.write(
            "ERROR: Jira user token not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(cjm.cfg.USER_TOKEN_ARG_NAME))
        return cjm.codes.CONFIGURATION_ERROR, None

    response = requests.get(
        url, params=params,
        auth=(cfg["jira"]["user"]["name"], cfg["jira"]["user"]["token"]))

    if response.status_code != 200:
        sys.stderr.write(
            "ERROR: The Jira API request ('{0:s}') failed with code {1:d}\n"
            "".format(url, response.status_code))
        return cjm.codes.REQUEST_ERROR, response

    return cjm.codes.NO_ERROR, response
