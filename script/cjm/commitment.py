# SPDX-License-Identifier: MIT
# Copyright (C) 2020-2021 Mobica Limited

"""Commitment data processing helpers"""

# Standard library imports
import json

# Third party imports
import jsonschema

# Project imports
import cjm.schema
import cjm.request


def load_data(cfg, commitment_file):
    """Load and validate given commitment data file"""
    schema = cjm.schema.load(cfg, "commitment.json")
    data = json.load(commitment_file)
    jsonschema.validate(data, schema)
    return data


def calc_total(issues):
    """Return sum of story points for given issues"""
    return sum([int(i["story points"]) for i in issues if i["story points"] is not None])
