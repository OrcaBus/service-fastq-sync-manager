#!/usr/bin/env python3
"""
Unit tests for handle_messages.py routing logic (_get_sfn_arn_env_var).

**Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5**

Tests the `_get_sfn_arn_env_var` function which determines which Step Function
ARN environment variable to use based on the payload structure.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

# Mock the aws_durable_execution_sdk_python modules before importing handle_messages,
# in case the package is not installed in the test environment.
sys.modules.setdefault(
    "aws_durable_execution_sdk_python",
    MagicMock(),
)
sys.modules.setdefault(
    "aws_durable_execution_sdk_python.config",
    MagicMock(),
)
sys.modules.setdefault(
    "aws_durable_execution_sdk_python.retries",
    MagicMock(),
)
sys.modules.setdefault(
    "aws_durable_execution_sdk_python.types",
    MagicMock(),
)

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

from handle_messages import (
    _get_sfn_arn_env_var,
    INITIALISE_TASK_TOKEN_FOR_FASTQ_ID_LIST_SFN_ARN_ENV_VAR,
    INITIALISE_TASK_TOKEN_FOR_FASTQ_SET_ID_SFN_ARN_ENV_VAR,
)


class TestGetSfnArnEnvVarRouting:
    """Unit tests for _get_sfn_arn_env_var routing logic."""

    def test_payload_with_fastq_set_only(self):
        """
        Payload containing only 'fastqSet' routes to the Fastq Set SFN ARN env var.

        Validates: Requirement 9.1
        """
        sfn_input = {
            "payload": {
                "fastqSet": "fqs.01ABC123",
                "requirements": {"hasFingerprint": True},
            }
        }
        result = _get_sfn_arn_env_var(sfn_input)
        assert result == INITIALISE_TASK_TOKEN_FOR_FASTQ_SET_ID_SFN_ARN_ENV_VAR

    def test_payload_with_fastq_id_list_only(self):
        """
        Payload containing only 'fastqIdList' routes to the Fastq ID List SFN ARN env var.

        Validates: Requirement 9.2
        """
        sfn_input = {
            "payload": {
                "fastqIdList": ["fqr.01XYZ789", "fqr.01XYZ790"],
                "requirements": {"hasActiveReadSet": True},
            }
        }
        result = _get_sfn_arn_env_var(sfn_input)
        assert result == INITIALISE_TASK_TOKEN_FOR_FASTQ_ID_LIST_SFN_ARN_ENV_VAR

    def test_payload_with_both_fields_fastq_set_takes_precedence(self):
        """
        Payload containing both 'fastqSet' and 'fastqIdList' routes to the Fastq Set
        SFN ARN env var — fastqSet takes precedence.

        Validates: Requirements 9.3, 9.5
        """
        sfn_input = {
            "payload": {
                "fastqSet": "fqs.01ABC123",
                "fastqIdList": ["fqr.01XYZ789"],
                "requirements": {"hasFingerprint": True},
            }
        }
        result = _get_sfn_arn_env_var(sfn_input)
        assert result == INITIALISE_TASK_TOKEN_FOR_FASTQ_SET_ID_SFN_ARN_ENV_VAR

    def test_payload_with_neither_field_raises_value_error(self):
        """
        Payload containing neither 'fastqSet' nor 'fastqIdList' raises ValueError,
        preventing any step function execution.

        Validates: Requirement 9.4
        """
        sfn_input = {
            "payload": {
                "requirements": {"hasFingerprint": True},
                "someOtherField": "value",
            }
        }
        with pytest.raises(ValueError, match="Missing routing field"):
            _get_sfn_arn_env_var(sfn_input)

    def test_missing_payload_key_raises_value_error(self):
        """
        When sfn_input has no 'payload' key, .get('payload', {}) returns an empty dict,
        causing ValueError since neither routing field is present.

        Validates: Requirement 9.4
        """
        sfn_input = {
            "taskToken": "some-token",
            "otherKey": "otherValue",
        }
        with pytest.raises(ValueError, match="Missing routing field"):
            _get_sfn_arn_env_var(sfn_input)

    def test_empty_payload_raises_value_error(self):
        """
        When the payload is an empty dict, neither routing field is present
        and ValueError is raised.

        Validates: Requirement 9.4
        """
        sfn_input = {"payload": {}}
        with pytest.raises(ValueError, match="Missing routing field"):
            _get_sfn_arn_env_var(sfn_input)
