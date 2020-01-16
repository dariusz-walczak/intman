#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Standard library imports
import argparse
import os
import re
import sys

# Third party imports
import simplejson
import xml.etree.ElementTree

# Local imports:
import stl.data
import stl.jira
import stl.sej
import stl.sprint


def parse_options(args):
    defaults = simplejson.load(open(".stl.json"))
    epic_list_default = defaults.get("epic list file", "epic-list.json")
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
        "--stl-data", action="store", metavar="PATH", dest="stl_data_path",
        default=stl_data_default,
        help="The stl data directory PATH (default: '{0:s}')".format(stl_data_default))
        
    parser.add_argument(
        "jira_xml", action="store", metavar="FILE",
        help="The jira search result xml FILE path")

    return parser.parse_args(args)


def main(options):
    cfg = {
        "stl_data_path": options.stl_data_path,
        "sow_data_path": options.sow_data_path
    }

    epic_list_file_name = os.path.join(options.sow_data_path, options.epic_list_file)

    with open(epic_list_file_name) as epic_list_file:
        prev_data = simplejson.load(epic_list_file)

    epic_map = dict(
        (epic_data["id"], epic_data)
        for epic_data in prev_data["jira list"])

    root = xml.etree.ElementTree.parse(options.jira_xml).getroot()

    for channel in root.iter("channel"):
        for item in channel.iter("item"):
            epic_id = item.find("key").text
            epic_name = stl.sej.extract_epic_name(item)

            if epic_id not in epic_map:
                sys.stderr.write(
                    "INFO: New epic will be added: '{0:s}'\n".format(epic_name))
                epic_map[epic_id] = {"id": epic_id, "name": epic_name}
            else:
                epic_data = epic_map[epic_id]
                if epic_data["name"] != epic_name:
                    sys.stderr.write(
                        "INFO: Epic '{0:s}' name will be changed from '{1:s}' to '{2:s}'\n"
                        "".format(epic_id, epic_data["name"], epic_name))
                    epic_data["name"] = epic_name

    curr_data = {
        "jira list": sorted(epic_map.values(), key=lambda e: stl.jira.sort_key(e["id"]))
    }

    with open(epic_list_file_name, "w") as epic_list_file:
        simplejson.dump(curr_data, epic_list_file, indent="    ", sort_keys=False)


if __name__ == '__main__':
    sys.exit(main(parse_options(sys.argv[1:])))
