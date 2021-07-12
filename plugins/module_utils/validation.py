# -*- coding: utf-8 -*-
# Copyright: (c) 2021, XLAB Steampunk <steampunk@xlab.si>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

from ansible.module_utils.six import text_type

from .errors import ServiceNowError


def _assert_str_or_none(param, val):
    if not isinstance(val, (str, text_type, type(None))):
        raise ServiceNowError(
            "Expected '{0}' to be text or None, got {1}".format(param, type(val))
        )


def missing_from_params_and_remote(params, module_params, record=None):
    """
    Given a list of params, module_params dict and a ServiceNow record, returns a
    list of params that are found neither in module_params, nor in the record itself (if it exists).
    Params must be a subset of record fields, and their values must be str or None.
    """
    missing = []
    if record and not set(params).issubset(record):
        raise ServiceNowError("Given parameters are not a subset of record fields")

    for p in params:
        if record:
            _assert_str_or_none(p, record[p])
        _assert_str_or_none(p, module_params[p])

        if module_params[p] is not None or (record and record[p]):
            continue
        missing.append(p)
    return missing


def check_value_incompatibility(
    incompatible_values, property_name, params, record=None
):
    """
    Given a list of incompatible values, a property name, params dict and a ServiceNow record, returns the check
    result and value of the checked property. Check result is True if property values aren't in the incompatible
    value list and False otherwise. The function assumes that new parameters override the record.
    """

    # Get value in effect
    value = params[property_name]
    if value is None:
        value = (record or {}).get(property_name)

    # Make sure value is not in the set of invalid values
    return value not in incompatible_values, value
