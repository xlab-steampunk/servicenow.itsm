# -*- coding: utf-8 -*-
# Copyright: (c) 2021, XLAB Steampunk <steampunk@xlab.si>
#
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

import sys

import pytest

from ansible_collections.servicenow.itsm.plugins.module_utils import validation, errors

pytestmark = pytest.mark.skipif(
    sys.version_info < (2, 7), reason="requires python2.7 or higher"
)


class TestMissingFromParamsAndRemote:
    @pytest.mark.parametrize(
        "params,module_params,record",
        [
            (["a"], dict(a="b"), None),  # module param only
            (
                ["a"],
                dict(a="b"),
                dict(),
            ),  # module param & remote record without desired
            (["a"], dict(a="b"), dict(a="b")),  # module param & remote record
            (["a"], dict(a=None), dict(a="b")),  # remote record only
            (
                ["a", "b"],
                dict(a=None, b="d"),
                dict(a="b", b=None),
            ),  # mixed with empty str
            (["a", "b"], dict(a="", b="d"), dict(a="b", b="")),  # mixed with None
        ],
    )
    def test_nothing_missing(self, params, module_params, record):
        assert [] == validation.missing_from_params_and_remote(
            params, module_params, record
        )

    @pytest.mark.parametrize(
        "params,module_params,record",
        [
            (["a"], dict(a=None), None),
            (["a"], dict(a=None), dict()),
            (["a"], dict(a=None), dict(a="")),
        ],
    )
    def test_missing(self, params, module_params, record):
        assert ["a"] == validation.missing_from_params_and_remote(
            params, module_params, record
        )

    def test_invalid_not_a_subset(self):
        with pytest.raises(errors.ServiceNowError, match="not a subset"):
            validation.missing_from_params_and_remote(
                ["a", "b"], dict(a=1, b=2), dict(a=1)
            )

    @pytest.mark.parametrize(
        "module_params,record",
        [
            (dict(a=True), dict(a="")),  # invalid module param type
            (dict(a=None), dict(a=True)),  # invalid record field type
        ],
    )
    def test_invalid_wrong_param_value_type(self, module_params, record):
        with pytest.raises(errors.ServiceNowError, match="text or None"):
            validation.missing_from_params_and_remote(["a"], module_params, record)


class TestValueIncompatibility:
    @pytest.mark.parametrize(
        "incompatible_states,property_name,params,record,resulting_property",
        [
            (
                ("a",),
                "p",
                dict(p="b"),
                None,
                "b",
            ),  # state set correctly during the module execution
            (
                ("a", "c"),
                "p",
                dict(p="b"),
                None,
                "b",
            ),  # state set correctly during the module execution
            (
                ("a",),
                "p",
                dict(p=None),
                dict(p="b"),
                "b",
            ),  # state already correct, parameters don't change said state
            (
                ("a", "c"),
                "p",
                dict(p="d"),
                dict(p="b"),
                "d",
            ),  # state correct, but value changed
            (
                ("a",),
                "p",
                dict(p="b"),
                dict(p="b"),
                "b",
            ),  # state set during module execution, also okay beforehand
            (
                ("a",),
                "p",
                dict(p="b"),
                dict(p="a"),
                "b",
            ),  # state used to be incompatible, is now set correctly
            (("a",), "p", dict(p=None), dict(), None),  # state not set
            (
                ("a",),
                "p",
                dict(p=None),
                None,
                None,
            ),  # state not set, record doesn't exist
        ],
    )
    def test_state_compatible(
        self, incompatible_states, property_name, params, record, resulting_property
    ):
        result = validation.check_value_incompatibility(
            incompatible_states, property_name, params, record
        )
        print(result)
        assert (True, resulting_property) == result

    @pytest.mark.parametrize(
        "incompatible_states,property_name,params,record,resulting_property",
        [
            (
                ("a",),
                "p",
                dict(p="a"),
                None,
                "a",
            ),  # state set incorrectly during the module execution
            (
                ("a", "c"),
                "p",
                dict(p="c"),
                None,
                "c",
            ),  # state set incorrectly during the module execution
            (
                ("a",),
                "p",
                dict(p=None),
                dict(p="a"),
                "a",
            ),  # state already incorrect and not corrected
            (
                ("a",),
                "p",
                dict(p="a"),
                dict(p="b"),
                "a",
            ),  # state correct in the record but not in the module
        ],
    )
    def test_state_not_compatible(
        self, incompatible_states, property_name, params, record, resulting_property
    ):
        assert (False, resulting_property) == validation.check_value_incompatibility(
            incompatible_states, property_name, params, record
        )
