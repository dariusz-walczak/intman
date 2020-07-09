"""General data and data file operations"""

# Standard library imports
import json
import sys

# Third party imports
import dateutil.parser
import isoweek
import jsonschema

# Project imports
import cjm.codes
import cjm.schema


def load(cfg, file_name, schema_name):
    """Load and validate specified json data file. Take care for handling of common file system
       errors"""
    try:
        with open(file_name) as data_file:
            schema = cjm.schema.load(cfg, schema_name)
            data = json.load(data_file)
            jsonschema.validate(data, schema)
    except IOError as e:
        sys.stderr.write(
            "ERROR: Team data file ('{0:s}') I/O error\n".format(file_name))
        sys.stderr.write("    {0}\n".format(e))
        raise cjm.codes.CjmError(cjm.codes.FILESYSTEM_ERROR)

    return data


def make_default_file_name(sprint_data, variant):
    """Construct default sprint data file name"""
    start_date = dateutil.parser.parse(sprint_data["start date"]).date()
    end_date = dateutil.parser.parse(sprint_data["end date"]).date()

    return "{0:s}_{1:d}-{2:s}_{3:s}.json".format(
        sprint_data["project"]["name"].lower(),
        isoweek.Week.withdate(start_date).year,
        cjm.sprint.generate_sprint_period_name(start_date, end_date).lower(), variant)


def make_flag_filter(field_name, filter_directive):
    """Make filter function callback to filter out items basing on the provided field and
    directive ("yes", "no", "all")"""
    return lambda item: (
        (filter_directive in ("all", "yes") and item[field_name]) or
        (filter_directive in ("all", "no") and not item[field_name]))


def make_defined_filter(field_name, filter_directive):
    """Make filter function callback to filter out items basing on the provided field (being or not
    being None) and the filter directive ("yes", "no", "all")"""
    return lambda item: (
        (filter_directive in ("all", "yes") and item[field_name] is not None) or
        (filter_directive in ("all", "no") and item[field_name] is None))


def add_warning(warnings, issue_key, message):
    """Add a new warning to the warning accumulator (warnings)"""
    warnings.setdefault(issue_key, []).append(
        {
            "key": issue_key,
            "msg": message
        }
    )
