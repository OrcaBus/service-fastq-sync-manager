#!/usr/bin/env python3
"""
Property-based tests for handle_messages.py routing logic.

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

Tests the `_get_sfn_arn_env_var` function which determines which Step Function
ARN environment variable to use based on the payload structure.
"""

import sys
from pathlib import Path

# Add the handle_messages Lambda directory to the path so we can import the module
sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[2]
        / "app"
        / "lambdas"
        / "handle_messages_py"
    ),
)

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from handle_messages import (
    _get_sfn_arn_env_var,
    INITIALISE_TASK_TOKEN_FOR_FASTQ_ID_LIST_SFN_ARN_ENV_VAR,
    INITIALISE_TASK_TOKEN_FOR_FASTQ_SET_ID_SFN_ARN_ENV_VAR,
)


# --- Strategies ---

# Strategy for arbitrary JSON-like values (used as field values in payloads)
json_values = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text(),
    lambda children: st.lists(children, max_size=3) | st.dictionaries(st.text(max_size=10), children, max_size=3),
    max_leaves=5,
)

# Strategy for additional arbitrary keys that are NOT routing fields
non_routing_keys = st.text(min_size=1, max_size=20).filter(
    lambda k: k not in ("fastqSet", "fastqIdList")
)

# Strategy for extra payload fields (arbitrary keys that aren't routing fields)
extra_payload_fields = st.dictionaries(non_routing_keys, json_values, max_size=5)

# Strategy for payloads containing 'fastqSet' (with or without 'fastqIdList')
payload_with_fastq_set = st.fixed_dictionaries(
    {"fastqSet": json_values},
    optional={"fastqIdList": json_values},
).flatmap(
    lambda d: extra_payload_fields.map(lambda extra: {**extra, **d})
)

# Strategy for payloads containing only 'fastqIdList' (no 'fastqSet')
payload_with_fastq_id_list_only = st.fixed_dictionaries(
    {"fastqIdList": json_values},
).flatmap(
    lambda d: extra_payload_fields.map(lambda extra: {**extra, **d})
)

# Strategy for payloads with neither routing field
payload_without_routing_fields = extra_payload_fields.filter(
    lambda d: "fastqSet" not in d and "fastqIdList" not in d
)


# --- Property 2: Message routing dispatches to correct step function ---


@pytest.mark.parametrize("_iteration", range(1))  # Hypothesis handles iterations
class TestProperty2MessageRouting:
    """
    Feature: fastq-set-sync, Property 2: message routing dispatches to correct step function

    **Validates: Requirements 9.1, 9.2, 9.3, 9.5**

    For any valid SQS message payload, the routing logic SHALL invoke
    `initialiseTaskTokenForFastqSetId` SFN if payload contains `fastqSet`
    (regardless of whether `fastqIdList` is also present), and SHALL invoke
    `initialiseTaskTokenForFastqIdList` SFN if payload contains `fastqIdList`
    but no `fastqSet`.
    """

    @given(payload=payload_with_fastq_set)
    @settings(max_examples=100)
    def test_fastq_set_field_routes_to_fastq_set_sfn(self, payload, _iteration):
        """
        When payload contains 'fastqSet' (with or without 'fastqIdList'),
        routing selects the INITIALISE_TASK_TOKEN_FOR_FASTQ_SET_ID_SFN_ARN env var.

        **Validates: Requirements 9.1, 9.5**
        """
        sfn_input = {"payload": payload}
        result = _get_sfn_arn_env_var(sfn_input)
        assert result == INITIALISE_TASK_TOKEN_FOR_FASTQ_SET_ID_SFN_ARN_ENV_VAR

    @given(payload=payload_with_fastq_id_list_only)
    @settings(max_examples=100)
    def test_fastq_id_list_only_routes_to_fastq_id_list_sfn(self, payload, _iteration):
        """
        When payload contains 'fastqIdList' but NOT 'fastqSet',
        routing selects the INITIALISE_TASK_TOKEN_FOR_FASTQ_ID_LIST_SFN_ARN env var.

        **Validates: Requirements 9.2, 9.3**
        """
        # Ensure no fastqSet key (strategy already guarantees this, but be explicit)
        assume("fastqSet" not in payload)
        sfn_input = {"payload": payload}
        result = _get_sfn_arn_env_var(sfn_input)
        assert result == INITIALISE_TASK_TOKEN_FOR_FASTQ_ID_LIST_SFN_ARN_ENV_VAR

    @given(
        fastq_set_value=json_values,
        fastq_id_list_value=json_values,
        extra=extra_payload_fields,
    )
    @settings(max_examples=100)
    def test_fastq_set_takes_precedence_when_both_present(
        self, fastq_set_value, fastq_id_list_value, extra, _iteration
    ):
        """
        When payload contains BOTH 'fastqSet' and 'fastqIdList',
        'fastqSet' takes precedence and routes to the Fastq Set SFN.

        **Validates: Requirements 9.5**
        """
        payload = {**extra, "fastqSet": fastq_set_value, "fastqIdList": fastq_id_list_value}
        sfn_input = {"payload": payload}
        result = _get_sfn_arn_env_var(sfn_input)
        assert result == INITIALISE_TASK_TOKEN_FOR_FASTQ_SET_ID_SFN_ARN_ENV_VAR


# --- Property 3: Payloads missing both routing fields are rejected ---


@pytest.mark.parametrize("_iteration", range(1))  # Hypothesis handles iterations
class TestProperty3InvalidPayloadRejection:
    """
    Feature: fastq-set-sync, Property 3: payloads missing both routing fields are rejected without execution

    **Validates: Requirements 9.4**

    For any message payload containing neither `fastqSet` nor `fastqIdList`,
    the routing logic SHALL raise a `ValueError` and SHALL NOT invoke any
    step function execution.
    """

    @given(payload=payload_without_routing_fields)
    @settings(max_examples=100)
    def test_missing_both_routing_fields_raises_value_error(self, payload, _iteration):
        """
        When payload contains neither 'fastqSet' nor 'fastqIdList',
        a ValueError is raised preventing any step function execution.

        **Validates: Requirements 9.4**
        """
        sfn_input = {"payload": payload}
        with pytest.raises(ValueError, match="Missing routing field"):
            _get_sfn_arn_env_var(sfn_input)

    @given(extra=extra_payload_fields)
    @settings(max_examples=100)
    def test_empty_payload_raises_value_error(self, extra, _iteration):
        """
        When the payload dict has arbitrary keys but no routing fields,
        a ValueError is raised.

        **Validates: Requirements 9.4**
        """
        # Explicitly ensure no routing fields
        payload = {k: v for k, v in extra.items() if k not in ("fastqSet", "fastqIdList")}
        sfn_input = {"payload": payload}
        with pytest.raises(ValueError, match="Missing routing field"):
            _get_sfn_arn_env_var(sfn_input)

    @given(data=st.data())
    @settings(max_examples=100)
    def test_missing_payload_key_uses_empty_dict_and_raises(self, data, _iteration):
        """
        When the sfn_input has no 'payload' key at all, the function
        uses an empty dict (via .get default) and raises ValueError since
        neither routing field is present.

        **Validates: Requirements 9.4**
        """
        # Generate an sfn_input without a 'payload' key
        other_keys = data.draw(
            st.dictionaries(
                st.text(min_size=1, max_size=10).filter(lambda k: k != "payload"),
                json_values,
                max_size=3,
            )
        )
        sfn_input = other_keys
        with pytest.raises(ValueError, match="Missing routing field"):
            _get_sfn_arn_env_var(sfn_input)
