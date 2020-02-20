#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Standard library imports
import sys
import json

# Third party imports
import jsonschema
import tabulate

# Project imports
import cjm.cfg
import cjm.schema
import cjm.codes
import cjm.sprint
import cjm.commitment
import cjm.request
import cjm.delivery

_COMMITMENT_PREFIX_ARG_NAME = "--prefix"

def parse_options(args):
    defaults = cjm.cfg.load_defaults()
    parser = cjm.cfg.make_common_parser(defaults)

    default_commitment_prefix = ""  # defaults.get("project", {}).get("key")

    parser.add_argument(
        _COMMITMENT_PREFIX_ARG_NAME, action="store", metavar="KEY", dest="commitment_prefix",
        default=default_commitment_prefix,
        help=(
            "Prefix to which the empty comment prefix will be changed{0:s}"
            "".format(cjm.cfg.fmt_dft(default_commitment_prefix))))

    parser.add_argument(
        "sprint_file", action="store",
        help=(
            "Path to the json sprint data file as generated by the {0:s} script and described by"
            " the {1:s} schema"
            "".format(cjm.SM_CREATE_SPRINT_FILE, cjm.schema.make_subpath("sprint.json"))))

    parser.add_argument(
        "delivery_file", action="store",
        help=(
            "Path to the json delivery report data file as generated by the {0:s} script and described by"
            " the {1:s} schema"
            "".format(cjm.SM_CREATE_GENERATE_DELIVERY_REPORT , cjm.schema.make_subpath("delivery.json"))))

    return parser.parse_args(args)


def get_issues_for_multiple_comments(cfg, sprint_data, comments_list):
    issues_with_closing_tag = {}
    for comment in comments_list:

        result_code, more_issues = cjm.sprint.request_issues_by_comment(
                cfg, "{0:s}/{1:s}".format(sprint_data["comment prefix"], comment ))
        
        if result_code:
            return result_code, []

        more_issues = {i["key"]: i for i in more_issues}
    
        issues_with_closing_tag.update(more_issues)
    
    return None, issues_with_closing_tag
    
def main(options):
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)

    # Load sprint data:

    try:
        with open(options.sprint_file) as sprint_file:
            sprint_data = cjm.sprint.load_data(cfg, sprint_file)
    except IOError as e:
        sys.stderr.write(
            "ERROR: Sprint data file ('{0:s}') I/O error\n".format(options.sprint_file))
        sys.stderr.write("    {0}\n".format(e))
        return cjm.codes.FILESYSTEM_ERROR

    cfg["sprint"]["id"] = sprint_data.get("id")
    cfg["project"]["key"] = sprint_data["project"]["key"]

    # Load delivery report file

    try:
        with open(options.delivery_file) as delivery_file:
            delivery_data = cjm.delivery.load_data(cfg, delivery_file)
    except IOError as e:
        sys.stderr.write(
            "ERROR: Sprint data file ('{0:s}') I/O error\n".format(options.delivery_file))
        sys.stderr.write("    {0}\n".format(e))
        return cjm.codes.FILESYSTEM_ERROR

    err, issues_with_openning_comment = get_issues_for_multiple_comments(cfg, sprint_data, ["Committed", "Extended"])

    if err:
        sys.stderr.write(
                "ERROR: Collecting issues wiht closing tags")
        return err

    no_opening_issues = list(filter(lambda i: i["key"] not in issues_with_openning_comment, delivery_data["issues"]))

    if no_opening_issues:
        print("Warining: Issues with no openning comment:") 
        print(tabulate.tabulate(
            [(p["id"], p["key"], p["summary"]) for p in no_opening_issues],
            headers=["Id", "Key", "Summary"], tablefmt="orgtbl"))
        print()


    result_code, delivered_issues = cjm.sprint.request_issues_by_comment(
        cfg, "{0:s}/Delivered".format(sprint_data["comment prefix"]))
    
    if result_code:
        sys.stderr.write(
                "ERROR: Collecting issues wiht comment {0:s}/Delivered failed".format(sprint_data["comment prefix"]))
        return result_code

    delivered_issues = {i["key"]: i for i in delivered_issues}

    err, issues_with_close_comment = get_issues_for_multiple_comments(cfg, sprint_data, ["Delivered", "NotDelivered", "Dropped"])

    if err:
        sys.stderr.write(
                "ERROR: Collecting issues wiht closing tags")
        return err

    no_closing_comment = list(filter(lambda i: i["key"] not in issues_with_close_comment, delivery_data["issues"]))

    print("No closing tag issues:")
    print(tabulate.tabulate(
        [(p["id"], p["key"], p["summary"]) for p in no_closing_comment],
        headers=["Id", "Key", "Summary"], tablefmt="orgtbl"))
    print("\n")
    

    return cjm.codes.NO_ERROR

if __name__ == "__main__":
    exit(main(parse_options(sys.argv[1:])))