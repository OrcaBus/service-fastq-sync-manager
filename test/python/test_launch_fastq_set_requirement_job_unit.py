#!/usr/bin/env python3
"""
Unit tests for the launchFastqSetRequirementJob Lambda.

Tests specific scenarios for the handler function covering:
- waitForBam=true prohibition (Requirements 5.1, 5.3)
- Job deduplication based on active states (Requirements 4.1, 4.3)
- HTTP error handling (Requirement 4.4)
- Successful job launch (Requirement 4.2)

Validates: Requirements 4.1, 4.2, 4.3, 4.4, 5.1, 5.3
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from requests import HTTPError

# --- Module Setup ---
# Mock orcabus_api_tools modules before importing the handler
_mock_modules = {
    "orcabus_api_tools": MagicMock(),
    "orcabus_api_tools.fastq": MagicMock(),
    "orcabus_api_tools.fastq.models": MagicMock(),
    "orcabus_api_tools.fastq_unarchiving": MagicMock(),
    "orcabus_api_tools.fastq_unarchiving.models": MagicMock(),
    "orcabus_api_tools.fastq_decompression": MagicMock(),
    "orcabus_api_tools.fastq_decompression.models": MagicMock(),
}

for mod_name, mock_mod in _mock_modules.items():
    sys.modules[mod_name] = mock_mod

# Add the layer source to the path so fastq_sync_tools can be imported
sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[2]
        / "app"
        / "layers"
        / "fastq_sync_tools_layer"
        / "src"
    ),
)

# Add the Lambda source directory to the path
sys.path.insert(
    0,
    str(
        Path(__file__).resolve().parents[2]
        / "app"
        / "lambdas"
        / "launch_fastq_set_requirement_job_py"
    ),
)

# Now import the handler module
import launch_fastq_set_requirement_job  # noqa: E402


class TestWaitForBamProhibition:
    """Tests for waitForBam=true strictly prohibiting API calls."""

    def test_wait_for_bam_returns_none_without_api_call(self):
        """
        When waitForBam=True, the handler returns None immediately
        without calling get_fastq_set_jobs or run_extract_fingerprint.

        Validates: Requirements 5.1, 5.3
        """
        with patch.object(
            launch_fastq_set_requirement_job, "get_fastq_set_jobs"
        ) as mock_get_jobs, patch.object(
            launch_fastq_set_requirement_job, "run_extract_fingerprint"
        ) as mock_run_extract:
            event = {
                "fastqSetId": "fqs.01ABC123",
                "requirementType": "hasFingerprint",
                "waitForBam": True,
            }

            result = launch_fastq_set_requirement_job.handler(event, None)

            assert result is None
            mock_get_jobs.assert_not_called()
            mock_run_extract.assert_not_called()


class TestNoExistingJobs:
    """Tests for the case when no existing jobs are present."""

    def test_no_existing_jobs_calls_extract_fingerprint(self):
        """
        When there are no existing jobs, run_extract_fingerprint is called
        with the fastq_set_id and the API response is returned.

        Validates: Requirements 4.1, 4.2
        """
        api_response = {"id": "job-001", "status": "PENDING", "fastqSetId": "fqs.01ABC123"}

        with patch.object(
            launch_fastq_set_requirement_job, "get_fastq_set_jobs"
        ) as mock_get_jobs, patch.object(
            launch_fastq_set_requirement_job, "run_extract_fingerprint"
        ) as mock_run_extract:
            mock_get_jobs.return_value = []
            mock_run_extract.return_value = api_response

            event = {
                "fastqSetId": "fqs.01ABC123",
                "requirementType": "hasFingerprint",
                "waitForBam": False,
            }

            result = launch_fastq_set_requirement_job.handler(event, None)

            mock_run_extract.assert_called_once_with(fastq_set_id="fqs.01ABC123")
            assert result == api_response


class TestActiveJobsBlockLaunching:
    """Tests for existing PENDING/RUNNING jobs blocking new launches."""

    def test_existing_pending_job_returns_none(self):
        """
        When a PENDING job exists, run_extract_fingerprint is not called
        and the handler returns None.

        Validates: Requirements 4.1, 4.3
        """
        with patch.object(
            launch_fastq_set_requirement_job, "get_fastq_set_jobs"
        ) as mock_get_jobs, patch.object(
            launch_fastq_set_requirement_job, "run_extract_fingerprint"
        ) as mock_run_extract:
            mock_get_jobs.return_value = [{"status": "PENDING"}]

            event = {
                "fastqSetId": "fqs.01ABC123",
                "requirementType": "hasFingerprint",
                "waitForBam": False,
            }

            result = launch_fastq_set_requirement_job.handler(event, None)

            assert result is None
            mock_run_extract.assert_not_called()

    def test_existing_running_job_returns_none(self):
        """
        When a RUNNING job exists, run_extract_fingerprint is not called
        and the handler returns None.

        Validates: Requirements 4.1, 4.3
        """
        with patch.object(
            launch_fastq_set_requirement_job, "get_fastq_set_jobs"
        ) as mock_get_jobs, patch.object(
            launch_fastq_set_requirement_job, "run_extract_fingerprint"
        ) as mock_run_extract:
            mock_get_jobs.return_value = [{"status": "RUNNING"}]

            event = {
                "fastqSetId": "fqs.01ABC123",
                "requirementType": "hasFingerprint",
                "waitForBam": False,
            }

            result = launch_fastq_set_requirement_job.handler(event, None)

            assert result is None
            mock_run_extract.assert_not_called()


class TestInactiveJobsDoNotBlock:
    """Tests for COMPLETED/SUCCEEDED/FAILED jobs NOT blocking new launches."""

    def test_completed_job_does_not_block(self):
        """
        A COMPLETED job does not block launching a new extraction job.

        Validates: Requirements 4.1, 4.3
        """
        with patch.object(
            launch_fastq_set_requirement_job, "get_fastq_set_jobs"
        ) as mock_get_jobs, patch.object(
            launch_fastq_set_requirement_job, "run_extract_fingerprint"
        ) as mock_run_extract:
            mock_get_jobs.return_value = [{"status": "COMPLETED"}]
            mock_run_extract.return_value = {"id": "job-new", "status": "PENDING"}

            event = {
                "fastqSetId": "fqs.01ABC123",
                "requirementType": "hasFingerprint",
                "waitForBam": False,
            }

            result = launch_fastq_set_requirement_job.handler(event, None)

            mock_run_extract.assert_called_once_with(fastq_set_id="fqs.01ABC123")
            assert result is not None

    def test_failed_job_does_not_block(self):
        """
        A FAILED job does not block launching a new extraction job.

        Validates: Requirements 4.1, 4.3
        """
        with patch.object(
            launch_fastq_set_requirement_job, "get_fastq_set_jobs"
        ) as mock_get_jobs, patch.object(
            launch_fastq_set_requirement_job, "run_extract_fingerprint"
        ) as mock_run_extract:
            mock_get_jobs.return_value = [{"status": "FAILED"}]
            mock_run_extract.return_value = {"id": "job-new", "status": "PENDING"}

            event = {
                "fastqSetId": "fqs.01ABC123",
                "requirementType": "hasFingerprint",
                "waitForBam": False,
            }

            result = launch_fastq_set_requirement_job.handler(event, None)

            mock_run_extract.assert_called_once_with(fastq_set_id="fqs.01ABC123")
            assert result is not None

    def test_succeeded_job_does_not_block(self):
        """
        A SUCCEEDED job does not block launching a new extraction job.

        Validates: Requirements 4.1, 4.3
        """
        with patch.object(
            launch_fastq_set_requirement_job, "get_fastq_set_jobs"
        ) as mock_get_jobs, patch.object(
            launch_fastq_set_requirement_job, "run_extract_fingerprint"
        ) as mock_run_extract:
            mock_get_jobs.return_value = [{"status": "SUCCEEDED"}]
            mock_run_extract.return_value = {"id": "job-new", "status": "PENDING"}

            event = {
                "fastqSetId": "fqs.01ABC123",
                "requirementType": "hasFingerprint",
                "waitForBam": False,
            }

            result = launch_fastq_set_requirement_job.handler(event, None)

            mock_run_extract.assert_called_once_with(fastq_set_id="fqs.01ABC123")
            assert result is not None


class TestHttpErrorHandling:
    """Tests for HTTP error scenarios returning None."""

    def test_http_error_from_extract_returns_none(self):
        """
        When run_extract_fingerprint raises HTTPError, the handler returns None.

        Validates: Requirement 4.4
        """
        with patch.object(
            launch_fastq_set_requirement_job, "get_fastq_set_jobs"
        ) as mock_get_jobs, patch.object(
            launch_fastq_set_requirement_job, "run_extract_fingerprint"
        ) as mock_run_extract:
            mock_get_jobs.return_value = []
            mock_run_extract.side_effect = HTTPError("500 Server Error")

            event = {
                "fastqSetId": "fqs.01ABC123",
                "requirementType": "hasFingerprint",
                "waitForBam": False,
            }

            result = launch_fastq_set_requirement_job.handler(event, None)

            assert result is None

    def test_http_error_from_get_jobs_returns_none(self):
        """
        When get_fastq_set_jobs raises HTTPError, the handler returns None
        without calling run_extract_fingerprint.

        Validates: Requirement 4.4
        """
        with patch.object(
            launch_fastq_set_requirement_job, "get_fastq_set_jobs"
        ) as mock_get_jobs, patch.object(
            launch_fastq_set_requirement_job, "run_extract_fingerprint"
        ) as mock_run_extract:
            mock_get_jobs.side_effect = HTTPError("503 Service Unavailable")

            event = {
                "fastqSetId": "fqs.01ABC123",
                "requirementType": "hasFingerprint",
                "waitForBam": False,
            }

            result = launch_fastq_set_requirement_job.handler(event, None)

            assert result is None
            mock_run_extract.assert_not_called()
