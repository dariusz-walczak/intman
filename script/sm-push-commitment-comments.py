#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Standard library imports
import sys

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


_COMMITMENT_PREFIX_ARG_NAME = "--prefix"

def make_comment_body(comment_text):
    return {
          "body": {
            "type": "doc",
            "version": 1,
            "content": [
                {
                "type": "paragraph",
                "content": [
                    {
                    "text": comment_text,
                    "type": "text"
                    }
                    ] 
                }
              ]
            }
          }

def main(options):
    cfg = cjm.cfg.apply_options(cjm.cfg.init_defaults(), options)
    cfg["issue"]["include unassigned"] = True

    # Load sprint data:

    try:
        with open(options.sprint_file) as sprint_file:
            sprint_data = cjm.sprint.load_data(cfg, sprint_file)
    except IOError as e:
        sys.stderr.write(
            "ERROR: Sprint data file ('{0:s}') I/O error\n".format(options.sprint_file))
        sys.stderr.write("    {0}\n".format(e))
        return cjm.codes.FILESYSTEM_ERROR

    sprint_schema = cjm.schema.load(cfg, "sprint.json")
    jsonschema.validate(sprint_data, sprint_schema)

    cfg["sprint"]["id"] = sprint_data.get("id")
    cfg["project"]["key"] = sprint_data["project"]["key"]

    if cfg["sprint"]["id"] is None:
        sys.stderr.write(
            "ERROR: The sprint id is not specified by the sprint data file ('{0:s}')\n"
            "".format(options.sprint_file))
        return cjm.codes.CONFIGURATION_ERROR

    # Load commitment data:

    try:
        with open(options.commitment_file) as commitment_file:
            commitment_data = cjm.commitment.load_data(cfg, commitment_file)
    except IOError as e:
        sys.stderr.write(
            "ERROR: Commitment data file ('{0:s}') I/O error\n".format(options.commitment_file))
        sys.stderr.write("    {0}\n".format(e))
        return cjm.codes.FILESYSTEM_ERROR

    commitment_schema = cjm.schema.load(cfg, "commitment.json")
    jsonschema.validate(commitment_data, commitment_schema)

    comment_to_be_added = sprint_data["comment prefix"] + "/Committed"

    # Retrieve all issues with the commitment comment added:
    result_code, all_issues_with_comments = cjm.sprint.request_issues_by_comment(
        cfg, comment_to_be_added)

    if result_code:
        return result_code

    commitment_issues = commitment_data["issues"]

    ids_commitment_issues = set([issue["id"] for issue in commitment_issues])
    ids_all_issues_with_comments = set([issue["id"] for issue in all_issues_with_comments])
    ids_commitment_issues_without_comments = ids_commitment_issues - ids_all_issues_with_comments

    if options.preview:
        print(tabulate.tabulate(
            [(i["id"], i["key"], i["summary"],comment_to_be_added ) for i in commitment_issues if i["id"] in ids_commitment_issues_without_comments],
            headers=["Id", "Key", "Summary", "Comment to be added"], tablefmt="orgtbl"))
        return 0

    for issue in commitment_issues:
        if issue["id"] in ids_commitment_issues_without_comments:
            comment_url = cjm.request.make_cj_url(cfg, "issue", str(issue["id"]), "comment")
            body = make_comment_body(comment_to_be_added)

            if options.verbose > 0:
                print(f"Posting '{comment_to_be_added}' to issue {issue['key']}")

            error, response = cjm.request.make_cj_post_request(cfg, comment_url, body)
            
            if cjm.codes.NO_ERROR != error:
                return error

    return cjm.codes.NO_ERROR


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
        "commitment_file", action="store",
        help=(
            "Path to the json commitment data file as generated by the {0:s} script and described"
            " by the {1:s} schema"
            "".format(cjm.SM_CREATE_COMMITMENT_FILE, cjm.schema.make_subpath("commitment.json"))))

    parser.add_argument('--verbose', '-v', action='count', default=0, help="Verbose")

    parser.add_argument(
        "--preview", action="store_true", dest="preview",
        help="Dont push comments but print whats about to happen to std output")

    return parser.parse_args(args)


if __name__ == "__main__":
    exit(main(parse_options(sys.argv[1:])))
