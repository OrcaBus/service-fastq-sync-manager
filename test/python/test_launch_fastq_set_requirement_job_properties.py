#!/usr/bin/env python3
"""
Property-based tests for the launchFastqSetRequirementJob Lambda.

Validates:
- Property 4: Job launch deduplication respects only active job states (Requirements 4.1, 4.3)
- Property 5: waitForBam=true strictly prohibits fingerprint extraction calls (Requirements 5.1, 5.3)
"""

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# --- Module Setup ---
# The Lambda imports `orcabus_api_tools.fastq` and `fastq_sync_tools` which are
# Lambda layer packages not available in the local dev environment.
# We create comprehensive mock modules in sys.modules before importing the handler.

# Create mock module hierarchy for orcabus_api_tools
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

# --- Strategies ---

# Job states as defined by the system
ACTIVE_JOB_STATES = ["PENDING", "RUNNING"]
INACTIVE_JOB_STATES = ["COMPLETED", "SUCCEEDED", "FAILED"]
ALL_JOB_STATES = ACTIVE_JOB_STATES + INACTIVE_JOB_STATES

# Strategy: Fastq Set IDs always start with "fqs."
fastq_set_id_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="._-"),
    min_size=1,
    max_size=30,
).map(lambda s: f"fqs.{s}")

# Strategy: a single job object with a status field
job_strategy = st.fixed_dictionaries(
    {"status": st.sampled_from(ALL_JOB_STATES)}
)

# Strategy: list of jobs (can be empty)
job_list_strategy = st.lists(job_strategy, min_size=0, max_size=10)

# Strategy: list of jobs containing ONLY inactive states (no PENDING/RUNNING)
inactive_only_job_list_strategy = st.lists(
    st.fixed_dictionaries({"status": st.sampled_from(INACTIVE_JOB_STATES)}),
    min_size=0,
    max_size=10,
)

# Strategy: list of jobs containing at least one active (PENDING or RUNNING) job
active_job_list_strategy = st.lists(
    job_strategy, min_size=1, max_size=10
).filter(lambda jobs: any(j["status"] in ACTIVE_JOB_STATES for j in jobs))


# --- Property 4 Tests ---


@pytest.mark.pbt
class TestProperty4JobLaunchDeduplication:
    """
    Feature: fastq-set-sync, Property 4: job launch deduplication respects only active job states

    For any Fastq Set ID and set of existing jobs, the Lambda SHALL call
    `runExtractFingerprint` if and only if no job with status `PENDING` or `RUNNING`
    exists. Jobs in `COMPLETED`, `SUCCEEDED`, or `FAILED` states SHALL NOT prevent launching.

    **Validates: Requirements 4.1, 4.3**
    """

    @settings(max_examples=100)
    @given(
        fastq_set_id=fastq_set_id_strategy,
        jobs=job_list_strategy,
    )
    def test_run_extract_fingerprint_called_iff_no_active_jobs(
        self, fastq_set_id: str, jobs: list
    ):
        """
        Property 4: runExtractFingerprint is called if and only if no PENDING or RUNNING
        jobs exist in the job list returned by get_fastq_set_jobs.

        **Validates: Requirements 4.1, 4.3**
        """
        has_active_job = any(j["status"] in ACTIVE_JOB_STATES for j in jobs)

        with patch.object(
            launch_fastq_set_requirement_job, "get_fastq_set_jobs"
        ) as mock_get_jobs, patch.object(
            launch_fastq_set_requirement_job, "run_extract_fingerprint"
        ) as mock_run_extract:
            mock_get_jobs.return_value = jobs
            mock_run_extract.return_value = {"id": "job-123", "status": "PENDING"}

            event = {
                "fastqSetId": fastq_set_id,
                "requirementType": "hasFingerprint",
                "waitForBam": False,
            }

            launch_fastq_set_requirement_job.handler(event, None)

            if has_active_job:
                # Should NOT call run_extract_fingerprint when active jobs exist
                mock_run_extract.assert_not_called()
            else:
                # Should call run_extract_fingerprint when no active jobs exist
                mock_run_extract.assert_called_once_with(fastq_set_id=fastq_set_id)

    @settings(max_examples=100)
    @given(
        fastq_set_id=fastq_set_id_strategy,
        jobs=inactive_only_job_list_strategy,
    )
    def test_inactive_jobs_do_not_block_launching(
        self, fastq_set_id: str, jobs: list
    ):
        """
        Property 4: Jobs in COMPLETED, SUCCEEDED, or FAILED states SHALL NOT prevent
        launching a new extraction job.

        **Validates: Requirements 4.1, 4.3**
        """
        with patch.object(
            launch_fastq_set_requirement_job, "get_fastq_set_jobs"
        ) as mock_get_jobs, patch.object(
            launch_fastq_set_requirement_job, "run_extract_fingerprint"
        ) as mock_run_extract:
            mock_get_jobs.return_value = jobs
            mock_run_extract.return_value = {"id": "job-456", "status": "PENDING"}

            event = {
                "fastqSetId": fastq_set_id,
                "requirementType": "hasFingerprint",
                "waitForBam": False,
            }

            result = launch_fastq_set_requirement_job.handler(event, None)

            # run_extract_fingerprint MUST be called since only inactive jobs exist
            mock_run_extract.assert_called_once_with(fastq_set_id=fastq_set_id)
            # And the result should be the API response
            assert result == {"id": "job-456", "status": "PENDING"}

    @settings(max_examples=100)
    @given(
        fastq_set_id=fastq_set_id_strategy,
        jobs=active_job_list_strategy,
    )
    def test_active_jobs_block_launching(
        self, fastq_set_id: str, jobs: list
    ):
        """
        Property 4: When at least one PENDING or RUNNING job exists,
        runExtractFingerprint SHALL NOT be called.

        **Validates: Requirements 4.1, 4.3**
        """
        with patch.object(
            launch_fastq_set_requirement_job, "get_fastq_set_jobs"
        ) as mock_get_jobs, patch.object(
            launch_fastq_set_requirement_job, "run_extract_fingerprint"
        ) as mock_run_extract:
            mock_get_jobs.return_value = jobs

            event = {
                "fastqSetId": fastq_set_id,
                "requirementType": "hasFingerprint",
                "waitForBam": False,
            }

            result = launch_fastq_set_requirement_job.handler(event, None)

            # run_extract_fingerprint MUST NOT be called when active jobs exist
            mock_run_extract.assert_not_called()
            # Result should be None
            assert result is None


# --- Property 5 Tests ---


@pytest.mark.pbt
class TestProperty5WaitForBamProhibition:
    """
    Feature: fastq-set-sync, Property 5: waitForBam=true strictly prohibits fingerprint extraction calls

    For any input where `waitForBam` is `true`, the Lambda SHALL NOT call
    `runExtractFingerprint`, regardless of fingerprint requirement status or any other condition.
    There is no timeout, fallback, or conditional override.

    **Validates: Requirements 5.1, 5.3**
    """

    @settings(max_examples=100)
    @given(
        fastq_set_id=fastq_set_id_strategy,
        jobs=job_list_strategy,
    )
    def test_wait_for_bam_never_calls_extract_fingerprint(
        self, fastq_set_id: str, jobs: list
    ):
        """
        Property 5: When waitForBam=true, runExtractFingerprint is NEVER called
        regardless of job states or requirement status.

        **Validates: Requirements 5.1, 5.3**
        """
        with patch.object(
            launch_fastq_set_requirement_job, "get_fastq_set_jobs"
        ) as mock_get_jobs, patch.object(
            launch_fastq_set_requirement_job, "run_extract_fingerprint"
        ) as mock_run_extract:
            mock_get_jobs.return_value = jobs

            event = {
                "fastqSetId": fastq_set_id,
                "requirementType": "hasFingerprint",
                "waitForBam": True,
            }

            result = launch_fastq_set_requirement_job.handler(event, None)

            # run_extract_fingerprint MUST NEVER be called when waitForBam=True
            mock_run_extract.assert_not_called()
            # get_fastq_set_jobs should also NOT be called (early return)
            mock_get_jobs.assert_not_called()
            # Result must be None
            assert result is None

    @settings(max_examples=100)
    @given(
        fastq_set_id=fastq_set_id_strategy,
    )
    def test_wait_for_bam_with_no_existing_jobs_still_prohibited(
        self, fastq_set_id: str
    ):
        """
        Property 5: Even when there are no existing jobs (ideal conditions for launching),
        waitForBam=true still prohibits the call.

        **Validates: Requirements 5.1, 5.3**
        """
        with patch.object(
            launch_fastq_set_requirement_job, "get_fastq_set_jobs"
        ) as mock_get_jobs, patch.object(
            launch_fastq_set_requirement_job, "run_extract_fingerprint"
        ) as mock_run_extract:
            mock_get_jobs.return_value = []  # No jobs at all

            event = {
                "fastqSetId": fastq_set_id,
                "requirementType": "hasFingerprint",
                "waitForBam": True,
            }

            result = launch_fastq_set_requirement_job.handler(event, None)

            # STILL must not call run_extract_fingerprint
            mock_run_extract.assert_not_called()
            # Should not even query jobs (early return on waitForBam=True)
            mock_get_jobs.assert_not_called()
            assert result is None
