#!/usr/bin/env python3

"""
Given a requirement item and a fastq set id, launch a job against the requirement item.

For hasFingerprint, we use the run_extract_fingerprint endpoint on the Fastq Manager API.

When waitForBam is true, we do NOT call runExtractFingerprint — the system waits for
an upstream FastqSetStateChange event with SOMALIER_UPDATED status instead.
"""

# Standard imports
from requests import HTTPError

# Orcabus API tools
from orcabus_api_tools.fastq import (
    get_fastq_set_jobs,
    run_extract_fingerprint,
)

# Layer imports
from fastq_sync_tools import FASTQ_SET_REQUIREMENT

# Job states that block launching a new extraction job
ACTIVE_JOB_STATES = {"PENDING", "RUNNING"}


def handler(event, context):
    """
    Launch a fingerprint extraction job for a Fastq Set.

    If waitForBam is true, immediately return None without any API calls.
    Otherwise, check for existing active jobs and launch extraction if none exist.

    :param event: Dict with fastqSetId, requirementType, and waitForBam
    :param context: Lambda context (unused)
    :return: API response on success, None on error or existing active job
    """
    # Get inputs
    fastq_set_id: str = event['fastqSetId']
    requirement_type: FASTQ_SET_REQUIREMENT = event['requirementType']
    wait_for_bam: bool = event.get('waitForBam', False)

    # Strict prohibition: when waitForBam is true, never call runExtractFingerprint
    if wait_for_bam:
        return None

    # Fetch existing jobs for the Fastq Set
    try:
        existing_jobs = get_fastq_set_jobs(fastq_set_id)
    except HTTPError:
        return None

    # Check if any active (PENDING or RUNNING) jobs exist
    # Jobs in COMPLETED, SUCCEEDED, or FAILED states do NOT block
    has_active_job = any(
        job.get('status') in ACTIVE_JOB_STATES
        for job in existing_jobs
    )

    if has_active_job:
        return None

    # No active jobs — launch fingerprint extraction (without BAM URI)
    try:
        return run_extract_fingerprint(fastq_set_id=fastq_set_id)
    except HTTPError:
        return None
