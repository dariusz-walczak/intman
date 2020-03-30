"""CLI presentation helpers"""

# Standard library imports
import enum

# Third party imports
import colorama


STATUS_CODES = enum.Enum(
    "StatusCodes",
    ("LOWEST", "LOWER", "LOW", "NEUTRAL", "HIGH", "HIGHER", "HIGHEST"))


def format_status(code):
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
    }.get(code, "")
