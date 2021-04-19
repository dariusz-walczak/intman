# Copyright © 2020-2021 Mobica Limited. All rights reserved.

"""CLI presentation helpers"""

# Standard library imports
import enum
import sys

# Third party imports
import colorama


STATUS_CODES = enum.Enum(
    "StatusCodes",
    ("LOWEST", "LOWER", "LOW", "NEUTRAL", "HIGH", "HIGHER", "HIGHEST"))


def cb_format_status_cell(importance_code, value):
    """Provide presentation string representing given status code"""
    return {
        STATUS_CODES.HIGHEST: (
            colorama.Fore.RED + colorama.Style.BRIGHT + "🡅🡅🡅" + colorama.Style.RESET_ALL),
        STATUS_CODES.HIGHER: (
            colorama.Fore.RED + "🡅🡅" + colorama.Style.RESET_ALL),
        STATUS_CODES.HIGH: (
            colorama.Fore.RED + colorama.Style.DIM + "🡅" + colorama.Style.RESET_ALL),
        STATUS_CODES.LOW: (
            colorama.Fore.BLUE + colorama.Style.DIM + "🡇" + colorama.Style.RESET_ALL),
        STATUS_CODES.LOWER: (
            colorama.Fore.BLUE + "🡇🡇" + colorama.Style.RESET_ALL),
        STATUS_CODES.LOWEST: (
            colorama.Fore.BLUE + colorama.Style.BRIGHT + "🡇🡇🡇" + colorama.Style.RESET_ALL)
    }.get(value, "")


IMPORTANCE_CODES = enum.Enum("ImportanceCodes", ("LOW", "NORMAL", "HIGH"))

def cb_format_default_cell(importance_code, value):
    """Format presentation string using given value and importance code

    :param code: One of the IMPORTANCE_CODES enum values; Influences cell color and brightness
    :param value: Value to be converted to string and annotated with the presentation directives
    """
    return {
        IMPORTANCE_CODES.LOW: (
            colorama.Fore.WHITE + colorama.Style.DIM + value + colorama.Style.RESET_ALL),
        IMPORTANCE_CODES.NORMAL: (
            colorama.Fore.WHITE + value + colorama.Style.RESET_ALL),
        IMPORTANCE_CODES.HIGH: (
            colorama.Fore.WHITE + colorama.Style.BRIGHT + value + colorama.Style.RESET_ALL)
    }.get(importance_code, value)


def cb_format_default_value(val):
    """Value formatting callback for default cell"""
    return "" if val is None else str(val)

def cb_format_ratio_value(ratio):
    """Value formatting callback for ratio cell"""
    return "" if ratio is None else "{0:14.2f}%".format(ratio)


def default_cell(key):
    """Get default cell specification to be provided to the format_row function"""
    return {
        "key": key,
        "value_cb": cb_format_default_value,
        "format_cb": cb_format_default_cell
    }

def status_cell(key):
    """Get status cell specification to be provided to the format_row function"""
    return {
        "key": key,
        "value_cb": None,
        "format_cb": cb_format_status_cell
    }

def ratio_cell(key):
    """Get ratio cell specification to be provided to the format_row function"""
    return {
        "key": key,
        "value_cb": cb_format_ratio_value,
        "format_cb": cb_format_default_cell
    }


def format_cell(importance_code, cell, row):
    """Format cell value using given cell specification and row data"""
    value_cb = cell["value_cb"]
    value_key = cell["key"]
    value_raw = row[value_key]
    format_cb = cell["format_cb"]
    value = value_raw if value_cb is None else value_cb(value_raw)
    return format_cb(importance_code, value)


def format_row(importance_code, cells, row):
    """Format cells values using given cells specification and row data"""
    return [format_cell(importance_code, cell, row) for cell in cells]


def color_issue_key(key):
    """Color issue key for output message construction purposes"""
    return "{0:s}{1:s}{2:s}".format(colorama.Fore.MAGENTA, key, colorama.Style.RESET_ALL)


def color_issue_comment(comment):
    """Color issue comment for output message construction purposes"""
    return "{0:s}{1:s}{2:s}".format(colorama.Fore.CYAN, comment, colorama.Style.RESET_ALL)


def color_emph(text):
    """Color emphasized text for output message construction purposes"""
    return "{0:s}{1}{2:s}".format(colorama.Style.BRIGHT, text, colorama.Style.RESET_ALL)


def print_data_warnings(warnings):
    """Print data processing warnings"""
    if warnings:
        sys.stderr.write(
            "{}{}WARNINGS:{}\n"
            "".format(colorama.Fore.RED, colorama.Style.BRIGHT, colorama.Style.RESET_ALL))

    for key in sorted(warnings.keys()):
        sys.stderr.write(
            "    {0:s}\n        {1:s}\n".format(
                color_issue_key(key),
                "\n        ".join([w["msg"] for w in warnings[key]])))
