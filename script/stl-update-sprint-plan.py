#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Standard library imports
import argparse
import os
import re
import sys
import json

# Third party imports
import xml.etree.ElementTree

# Local imports:
import stl.data
import stl.onj
import stl.sprint


_SPRINT_DATA_OPT = "--sprint-data"


def parse_options(args):
    defaults = json.load(open(".stl.json"))
    epic_list_default = defaults.get("epic list file", "epic-list.json")
    sprint_list_default = defaults.get("sprint list file", "sprint-list.json")
    sow_data_default = defaults.get("sow data path", ".")
    stl_data_default = defaults.get("stl_data path", "data/stl")

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--sow-data", action="store", metavar="PATH", dest="sow_data_path",
        default=sow_data_default,
        help="The sow data directory PATH (default: '{0:s}')".format(sow_data_default))
    parser.add_argument(
        "--epic-list", action="store", metavar="FILE", dest="epic_list_file",
        default="epic-list.json",
        help="The sow epic list FILE name (default: '{0:s}')".format(epic_list_default))
    parser.add_argument(
        "--sprint-list", action="store", metavar="FILE", dest="sprint_list_file",
        default="sprint-list.json",
        help="The sow sprint list FILE name (default: '{0:s}')".format(sprint_list_default))
    parser.add_argument(
        "--stl-data", action="store", metavar="PATH", dest="stl_data_path",
        default=stl_data_default,
        help="The stl data directory PATH (default: '{0:s}')".format(stl_data_default))
    parser.add_argument(
        _SPRINT_DATA_OPT, action="store", metavar="PATH", dest="sprint_data_path",
        help=(
            "The sprint data directory PATH (if not specified it will be attempted to be retrieved"
            " from the sow directory files)"))
    parser.add_argument(
        "jira_xml", action="store", metavar="FILE",
        help="The jira search result xml FILE path")

    return parser.parse_args(args)


def extract_sprint_data(channel_element, sprint_data):
    raw_sprint_name = channel_element.find("title").text

    name_match = re.search(r"WW(?P<ww1>\d\d)-WW(?P<ww2>\d\d)", raw_sprint_name)

    if name_match is not None:
        sprint_data["ww_first"] = int(name_match.group("ww1"))
        sprint_data["ww_last"] = int(name_match.group("ww2"))

    return sprint_data


def main(options):
    cfg = {
        "stl_data_path": options.stl_data_path,
        "sow_data_path": options.sow_data_path,
        "sprint_data_path": None
    }

    sprint_data = stl.data.sprint_data_init()
    team_data = stl.data.team_data_load(cfg)
    account_map = stl.data.account_map_create(team_data, "ONJ")

    root = xml.etree.ElementTree.parse(options.jira_xml).getroot()

    # First channel iteration to determine the sprint and sprint data path:
    for channel_idx, channel in enumerate(root.iter("channel")):
        if not channel_idx:
            sprint_data = extract_sprint_data(channel, sprint_data)
        else:
            sys.stderr.write(
                "WARNING: Unsupported case of multiple channels encountered. Analyze the xml"
                " content to determine what it means and then handle the case in the script code")

    if options.sprint_data_path is not None:
        sys.stderr.write(
            "INFO: The sprint data path ('{0:s}') is taken from the '{1:s}' command line argument."
            "\n".format(options.sprint_data_path, _SPRINT_DATA_OPT))
    else:
        if sprint_data["ww_first"] is None or sprint_data["ww_last"] is None:
            sys.stderr.write(
                "ERROR: Missing the '{0:s}' command line argument".format(_SPRINT_DATA_OPT))
            sys.exit(1)
        else:
            sow_sprint_list_file_name = os.path.join(
                cfg["sow_data_path"], options.sprint_list_file)
            sys.stderr.write(
                "INFO: The sprint identification data will be retrieved from the sow sprint list"
                " file ({0:s})\n".format(sow_sprint_list_file_name))

        sys.stderr.write(
            "INFO: The sprint identification data couldn't be retrieved from the input xml file."
            " The '{0:s}' command line argument becomes required.\n".format(_SPRINT_DATA_OPT))

        cfg["sprint_data_path"] = options.sprint_data_path

    ticket_data = []
    for channel_idx, channel in enumerate(root.iter("channel")):
        ticket_data = [
            {
                "id": item.find("key").text,
                "name": item.find("summary").text,
                "sp": stl.onj.extract_story_point_number(item),
                "status": stl.onj.status_to_code(item.find("status").text),
                "priority index": stl.onj.priority_to_idx(item.find("priority").text),
                "assignee code": account_map.get(
                    item.find("assignee").get("username"), {"code": None})["code"]
            }
            for item in channel.iter("item")
        ]

    sprint_json = stl.sprint.plan_generate(team_data, sprint_data, ticket_data)

    print(json.dumps(sprint_json, indent="    ", sort_keys=False))


if __name__ == '__main__':
    sys.stderr.write("TODO: ADD SUPPORT FOR UNASSIGNED ITEMS\n")
    sys.stderr.write("TODO: ADD SUPPORT FOR TASK STATUS\n")
    sys.stderr.write("TODO: PUT CAPACITY IN SEPARATE JSON FILE\n")

    sys.exit(main(parse_options(sys.argv[1:])))
