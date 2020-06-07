"""Delivery data processing helpers"""

# Standard library imports
import decimal
import json

# Third party imports
import jsonschema

# Project imports
import cjm.presentation
import cjm.request
import cjm.schema


def load_data(cfg, delivery_file):
    """Load and validate given delivery data file"""
    schema = cjm.schema.load(cfg, "delivery.json")
    data = json.load(delivery_file)
    jsonschema.validate(data, schema)
    return data


def determine_alien_status(delivery_value):
    """Determine delivery ratio status code for given delivery value with the assumption that
    related capacity is zero"""
    if delivery_value > 20:
        return cjm.presentation.STATUS_CODES.HIGHEST
    elif delivery_value > 10:
        return cjm.presentation.STATUS_CODES.HIGHER
    elif delivery_value > 0:
        return cjm.presentation.STATUS_CODES.HIGH
    return cjm.presentation.STATUS_CODES.NEUTRAL


def determine_ratio_status(ratio):
    """Determine commitment ratio status code for given commitment ratio"""
    # pylint: disable=too-many-return-statements
    if ratio < 60:
        return cjm.presentation.STATUS_CODES.LOWEST
    elif ratio < 80:
        return cjm.presentation.STATUS_CODES.LOWER
    elif ratio < 90:
        return cjm.presentation.STATUS_CODES.LOW
    elif ratio > 140:
        return cjm.presentation.STATUS_CODES.HIGHEST
    elif ratio > 120:
        return cjm.presentation.STATUS_CODES.HIGHER
    elif ratio > 100:
        return cjm.presentation.STATUS_CODES.HIGH
    return cjm.presentation.STATUS_CODES.NEUTRAL


def determine_summary(delivery_value, commitment_value):
    """Determine commitment summary for given delivery and commitment values"""
    if commitment_value > 0:
        ratio = (
            decimal.Decimal("{0:d}.0000".format(delivery_value)) /
            decimal.Decimal(commitment_value) * 100)
        ratio = ratio.quantize(decimal.Decimal("0.00"), decimal.ROUND_HALF_UP)
        status = determine_ratio_status(ratio)
    else:
        ratio = None
        status = determine_alien_status(delivery_value - commitment_value)

    return {
        "commitment": commitment_value,
        "delivery": delivery_value,
        "delivery ratio": ratio,
        "delivery status": status
    }
