"""Jira API request wrappers and helpers"""

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
_CJ_GADGET_PATH = "/rest/gadget/1.0"
_CJ_ISSUE_PATH = "/browse"

def _get_jira_host(cfg):
    """Retrieve the jira host name from given configuration data. Raise an exception if it is not
    specified"""
    if cfg["jira"]["host"] is None:
        sys.stderr.write(
            "ERROR: Jira host name not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(cjm.cfg.HOST_NAME_ARG_NAME))
        raise cjm.codes.CjmError(cjm.codes.CONFIGURATION_ERROR)
    return cfg["jira"]["host"]


def _get_jira_scheme(cfg):
    """Retrieve the jira scheme from given configuration data. Raise an exception if it is not
    specified"""
    if cfg["jira"]["scheme"] is None:
        sys.stderr.write(
            "ERROR: Jira scheme name not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(cjm.cfg.SCHEME_ARG_NAME))
        raise cjm.codes.CjmError(cjm.codes.CONFIGURATION_ERROR)
    return cfg["jira"]["scheme"]


def make_cj_url(cfg, *resource_path):
    """Construct a Cloud Jira API url"""
    url_parts = (
        _get_jira_scheme(cfg), _get_jira_host(cfg), "/".join((_CJ_API_PATH, *resource_path)),
        "", "", "")
    return urllib.parse.urlunparse(url_parts)


def make_cj_agile_url(cfg, *resource_path):
    """Construct a Jira Agile API url"""
    url_parts = (
        _get_jira_scheme(cfg), _get_jira_host(cfg), "/".join((_CJ_AGILE_PATH, *resource_path)),
        "", "", "")
    return urllib.parse.urlunparse(url_parts)


def make_cj_gadget_url(cfg, *resource_path):
    """Construct a Jira Gadget API url"""
    url_parts = (
        _get_jira_scheme(cfg), _get_jira_host(cfg), "/".join((_CJ_GADGET_PATH, *resource_path)),
        "", "", "")
    return urllib.parse.urlunparse(url_parts)


def make_cj_issue_url(cfg, *resource_path):
    """Construct a Jira issue page url"""
    url_parts = (
        _get_jira_scheme(cfg), _get_jira_host(cfg), "/".join((_CJ_ISSUE_PATH, *resource_path)),
        "", "", "")
    return urllib.parse.urlunparse(url_parts)


def make_cj_request(cfg, url, params=None, tolerate_404=True):
    """Make Cloud Jira API GET request"""
    params = {} if params is None else params

    if cfg["jira"]["user"]["name"] is None:
        sys.stderr.write(
            "ERROR: Jira user name not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(cjm.cfg.USER_NAME_ARG_NAME))
        raise cjm.codes.CjmError(cjm.codes.CONFIGURATION_ERROR)

    if cfg["jira"]["user"]["token"] is None:
        sys.stderr.write(
            "ERROR: Jira user token not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(cjm.cfg.USER_TOKEN_ARG_NAME))
        raise cjm.codes.CjmError(cjm.codes.CONFIGURATION_ERROR)

    response = requests.get(
        url, params=params,
        auth=(cfg["jira"]["user"]["name"], cfg["jira"]["user"]["token"]))

    if (response.status_code != 200) and not (response.status_code == 404 and tolerate_404):
        sys.stderr.write(
            "ERROR: The Jira API request ('{0:s}') failed with code {1:d}\n"
            "".format(url, response.status_code))
        raise cjm.codes.CjmError(cjm.codes.REQUEST_ERROR)

    return response


def make_cj_post_request(cfg, url, json):
    """Make Cloud Jira API POST request"""
    if cfg["jira"]["user"]["name"] is None:
        sys.stderr.write(
            "ERROR: Jira user name not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(cjm.cfg.USER_NAME_ARG_NAME))
        raise cjm.codes.CjmError(cjm.codes.CONFIGURATION_ERROR)

    if cfg["jira"]["user"]["token"] is None:
        sys.stderr.write(
            "ERROR: Jira user token not specified. Use the '{0:s}' CLI option or the defaults"
            " file to specify it\n".format(cjm.cfg.USER_TOKEN_ARG_NAME))
        raise cjm.codes.CjmError(cjm.codes.CONFIGURATION_ERROR)

    response = requests.post(
        url, json=json,
        auth=(cfg["jira"]["user"]["name"], cfg["jira"]["user"]["token"]))

    if not response.ok:
        sys.stderr.write(
            "ERROR: The Jira API request ('{0:s}') failed with code {1:d}\n"
            "".format(url, response.status_code))
        raise cjm.codes.CjmError(cjm.codes.REQUEST_ERROR)

    return response
