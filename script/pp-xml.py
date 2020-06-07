#!/usr/bin/env python3

# Standard library imports
import argparse
import sys
import xml.dom.minidom


def parse_options(args):
    """Parse command line options"""
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "xml_file", action="store",
        help="Path to the xml file to be pretty printed")

    return parser.parse_args(args)

def main(options):
    """Entry function"""

    dom = xml.dom.minidom.parse(options.xml_file)
    print(dom.toprettyxml())

    return 0


if __name__ == '__main__':
    sys.exit(main(parse_options(sys.argv[1:])))
