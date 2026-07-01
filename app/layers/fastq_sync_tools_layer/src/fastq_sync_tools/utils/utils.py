#!/usr/bin/env python3

"""
Bunch of useful helper functions for lambdas in the fastq sync service
"""

# Standard library imports
import os
from typing import Dict, Optional, List, Tuple, Union
import logging
from requests import HTTPError

# Layer imports
from orcabus_api_tools.fastq import (
    get_fastq_jobs,
    run_qc_stats,
    run_file_compression_stats,
    run_ntsm, run_read_count_stats,
    to_fastq_list_row
)
from orcabus_api_tools.fastq.models import (
    Job, JobType,
    Fastq
)
from orcabus_api_tools.fastq_unarchiving import (
    create_job as create_unarchiving_job,
    get_job_list_for_fastq
)
from orcabus_api_tools.fastq_unarchiving.models import (
    Job as UnarchivingJob,
)

# Local imports
from .globals import (
    REQUIREMENT,
    ACTIVE_STORAGE_CLASSES
)

from .exceptions import ContextNotEligibleError

logger = logging.getLogger(__name__)


def has_active_readset(fastq_obj: Fastq) -> bool:
    if fastq_obj['readSet'] is None:
        return False

    readset_objects = list(filter(
        lambda readset_iter_: readset_iter_ is not None,
        [fastq_obj['readSet']['r1'], fastq_obj['readSet']['r2']]
    ))

    for readset_object in readset_objects:
        # If the storage class is not in the active storage classes or
        if readset_object['storageClass'] not in ACTIVE_STORAGE_CLASSES:
            return False

    return True


def has_active_readset_in_context(fastq_obj: Fastq, bucket: str, prefix: str) -> bool:
    """
    Check if all non-null ReadSet objects for a FASTQ reside in the given bucket
    with keys starting with the given prefix AND are in active storage.

    Returns True if every non-null ReadSet object (r1, r2) has:
    - storageClass in ACTIVE_STORAGE_CLASSES
    - bucket equals the given bucket
    - key starts with the given prefix

    Returns False if readSet is None or no non-null ReadSet objects exist.
    """
    if fastq_obj['readSet'] is None:
        return False

    # Try running to_fastq_list_row with the bucket and prefix context
    try:
        to_fastq_list_row(
            fastq_id=fastq_obj['id'],
            bucket=bucket,
            key_prefix=prefix,
        )
    except HTTPError:
        return False
    return True


def has_qc(fastq_obj: Fastq) -> bool:
    return fastq_obj['qc'] is not None


def has_fingerprint(fastq_obj: Fastq) -> bool:
    return fastq_obj['ntsm'] is not None


def has_compression_metadata(fastq_obj: Fastq) -> bool:
    # Check active readset
    if not has_active_readset(fastq_obj):
        return False

    # Can assert we have an active readset and that the readset is not None

    # Let's check if the compression format is ORA, if not, we can assume that the compression metadata
    # Condition is satisfied
    if fastq_obj['readSet']['compressionFormat'] != 'ORA':
        return True

    # If the compression format is ORA, then we need to check if the compression metadata is present
    readset_objects = list(filter(
        lambda readset_iter_: readset_iter_ is not None,
        [fastq_obj['readSet']['r1'], fastq_obj['readSet']['r2']]
    ))

    for readset_object in readset_objects:
        if readset_object['gzipCompressionSizeInBytes'] is None or readset_object['rawMd5sum'] is None:
            return False

    # If we got to here then the compression metadata is present in all readsets for this fastq list row
    return True


def has_read_count_metadata(fastq_obj: Fastq) -> bool:
    if fastq_obj['readCount'] is None or fastq_obj['baseCountEst'] is None:
        return False
    return True


def check_fastq_job(fastq_id: str, job_type: JobType) -> bool:
    """
    Check the fastq doesn't already have jobs running for this particular type
    :param fastq_id:
    :param job_type:
    :return:
    """
    return (
            len(
                list(filter(
                    lambda job_iter_: (
                            (
                                    job_iter_['jobType'] == job_type
                            ) and
                            (
                                    job_iter_['status'] in ['PENDING', 'RUNNING']
                            )
                    ),
                    get_fastq_jobs(fastq_id)
                ))
            ) == 0
    )


def check_fastq_unarchiving_job(fastq_id: str) -> bool:
    """
    Check that the fastq doesn't already have an unarchiving job running
    Return True if there is no unarchiving jobs running for this fastq list row id
    Return False if there are unarchiving jobs running for this fastq list row id
    :param fastq_id:
    :return:
    """
    return (
            (
                    len(get_job_list_for_fastq(fastq_id, 'PENDING')) == 0
            ) and
            (
                    len(get_job_list_for_fastq(fastq_id, 'RUNNING')) == 0
            )
    )


def run_fastq_job(fastq: Fastq, job_type: JobType) -> Optional[Job]:
    """
    Run a job for a fastq
    :param fastq:
    :param job_type:
    :return:
    """
    # Check that the fastq list row has an active read set
    if not has_active_readset(fastq):
        logger.warning("No active read set for fastq %s" % fastq)
        return None

    # Check if the job is already running
    if not check_fastq_job(fastq['id'], job_type):
        return None

    # Create the job
    if job_type == 'QC':
        return run_qc_stats(fastq_id=fastq['id'])

    if job_type == 'NTSM':
        return run_ntsm(fastq_id=fastq['id'])

    if job_type == 'FILE_COMPRESSION':
        return run_file_compression_stats(fastq_id=fastq['id'])

    if job_type == 'READ_COUNT':
        return run_read_count_stats(fastq_id=fastq['id'])

    raise ValueError(f"Unknown job type: {job_type}")


def run_fastq_unarchiving_job(fastq: Fastq) -> Optional[UnarchivingJob]:
    return create_unarchiving_job(
        fastq_ids=[
            fastq['id']
        ],
        job_type='S3_UNARCHIVING'
    )


def check_fastq_against_requirements_list(
        fastq_obj: Fastq,
        requirements: List[REQUIREMENT],
        is_unarchiving_allowed: bool = False
) -> Tuple[List[REQUIREMENT], List[REQUIREMENT]]:
    """
    Given a fastq list row and the requirements, split requirements into two lists, one that is satisfied and one that is not
    """

    satisfied_requirements = []
    unsatisfied_requirements = []

    # First check we can even run any of the jobs
    # If data is archived and unarchiving is not allowed, we cannot run any jobs
    if (
            not is_unarchiving_allowed
            and 'hasActiveReadSet' in requirements
            and (not has_active_readset(fastq_obj))
            and fastq_obj['readSet'] is not None
    ):
        raise ValueError("Fastq object is archived but unarchiving is not specified in the fastq sync service")

    # Just a large if else block to check the requirements
    for requirement_iter_ in requirements:
        # Check read set
        if requirement_iter_ == 'hasActiveReadSet':
            if has_active_readset(fastq_obj):
                satisfied_requirements.append(requirement_iter_)
            else:
                unsatisfied_requirements.append(requirement_iter_)

        # Check qc
        if requirement_iter_ == 'hasQc':
            if has_qc(fastq_obj):
                satisfied_requirements.append(requirement_iter_)
            else:
                unsatisfied_requirements.append(requirement_iter_)

        # Check fingerprint
        if requirement_iter_ == 'hasFingerprint':
            if has_fingerprint(fastq_obj):
                satisfied_requirements.append(requirement_iter_)
            else:
                unsatisfied_requirements.append(requirement_iter_)

        # Check compression metadata
        if requirement_iter_ == 'hasFileCompressionInformation':
            if has_compression_metadata(fastq_obj):
                satisfied_requirements.append(requirement_iter_)
            else:
                unsatisfied_requirements.append(requirement_iter_)

        # Check read-count metadata
        if requirement_iter_ == 'hasReadCountInformation':
            if has_read_count_metadata(fastq_obj):
                satisfied_requirements.append(requirement_iter_)
            else:
                unsatisfied_requirements.append(requirement_iter_)


    return satisfied_requirements, unsatisfied_requirements


def check_fastq_list_against_requirements_list(
        fastq_list: List[Fastq],
        requirements: List[REQUIREMENT],
        is_unarchiving_allowed: bool = False,
) -> Tuple[List[REQUIREMENT], List[REQUIREMENT]]:
    """
    Given a list of fastqs and the requirements,
    split the fastq list into two lists,
    one that is satisfied (for all fastqs) and one that is not (for at least one fastq)
    """

    # Start with all requirements satisfied
    satisfied_requirements = set(requirements)

    # For each fastq object in the list, check against the requirements
    for fastq_obj in fastq_list:
        # Check if the fastq object has the requirements satisfied
        satisfied_requirements_iter_, unsatisfied_requirements_iter_ = check_fastq_against_requirements_list(
            fastq_obj,
            requirements,
            is_unarchiving_allowed
        )

        # If there are no unsatisfied requirements, continue to the next fastq object
        if len(unsatisfied_requirements_iter_) == 0:
            continue

        # Remove any unsatisfied requirements from
        # the satisfied requirements from the set
        # Since all fastq objects must satisfy the requirements
        for unsatisfied_requirement_iter_ in unsatisfied_requirements_iter_:
            if unsatisfied_requirement_iter_ in satisfied_requirements:
                # Remove the requirement from the satisfied requirements
                satisfied_requirements.remove(unsatisfied_requirement_iter_)

    # The list of unsatisfied requirements is the difference
    # between the original requirements and the satisfied requirements
    unsatisfied_requirements = list(set(requirements) - satisfied_requirements)

    return list(satisfied_requirements), unsatisfied_requirements


def get_pipeline_cache_config() -> Tuple[str, str]:
    """
    Read and validate PIPELINE_CACHE_BUCKET and PIPELINE_CACHE_PREFIX from environment.
    Returns (pipeline_cache_bucket, byob_environment).
    Raises RuntimeError if either is missing or empty.
    """
    pipeline_cache_bucket = os.environ.get("PIPELINE_CACHE_BUCKET", "")
    byob_environment = os.environ.get("PIPELINE_CACHE_PREFIX", "")

    if not pipeline_cache_bucket:
        raise RuntimeError("Missing required environment variable: PIPELINE_CACHE_BUCKET")
    if not byob_environment:
        raise RuntimeError("Missing required environment variable: PIPELINE_CACHE_PREFIX")

    return pipeline_cache_bucket, byob_environment


def validate_has_active_readset_input(
        has_active_readset_value: Union[bool, dict]
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate and normalize hasActiveReadSet input.

    Args:
        has_active_readset_value: Either a boolean or a dict with 'bucket' and 'prefix'.

    Returns:
        Tuple of (is_context_aware, bucket_or_none, prefix_or_none).
        - For boolean True: (False, None, None) — context-free check
        - For dict: (True, bucket, prefix) — context-aware check

    Raises:
        ValueError: If input is boolean False (should be excluded by caller),
                    or if dict has missing/empty/invalid bucket or prefix,
                    or if input is neither bool nor dict.
    """
    # Handle boolean input
    if isinstance(has_active_readset_value, bool):
        if has_active_readset_value:
            return (False, None, None)
        else:
            raise ValueError(
                "hasActiveReadSet value is False; "
                "this requirement should be excluded from the requirements list"
            )

    # Handle dict input
    if isinstance(has_active_readset_value, dict):
        # Check 'bucket' key exists
        if 'bucket' not in has_active_readset_value:
            raise ValueError(
                "hasActiveReadSet object is missing required attribute: 'bucket'"
            )

        # Check 'prefix' key exists
        if 'prefix' not in has_active_readset_value:
            raise ValueError(
                "hasActiveReadSet object is missing required attribute: 'prefix'"
            )

        bucket = has_active_readset_value['bucket']
        prefix = has_active_readset_value['prefix']

        # Validate bucket is a string
        if not isinstance(bucket, str):
            raise ValueError("hasActiveReadSet 'bucket' must be a string")

        # Validate prefix is a string
        if not isinstance(prefix, str):
            raise ValueError("hasActiveReadSet 'prefix' must be a string")

        # Check bucket is non-empty after strip
        if not bucket.strip():
            raise ValueError(
                "hasActiveReadSet 'bucket' must not be empty or whitespace-only"
            )

        # Check prefix is non-empty after strip
        if not prefix.strip():
            raise ValueError(
                "hasActiveReadSet 'prefix' must not be empty or whitespace-only"
            )

        # Check bucket length (1-63)
        if len(bucket) > 63:
            raise ValueError(
                f"hasActiveReadSet 'bucket' exceeds maximum length of 63 characters "
                f"(got {len(bucket)})"
            )

        # Check prefix length (1-1024)
        if len(prefix) > 1024:
            raise ValueError(
                f"hasActiveReadSet 'prefix' exceeds maximum length of 1024 characters "
                f"(got {len(prefix)})"
            )

        return (True, bucket, prefix)

    # Neither bool nor dict
    raise ValueError(
        f"hasActiveReadSet must be a boolean or an object with 'bucket' and 'prefix', "
        f"got {type(has_active_readset_value).__name__}"
    )


def is_allowed_context(bucket: str, prefix: str) -> bool:
    """
    Check if the given bucket and prefix match the allowed pipeline-cache context.

    Returns True if bucket equals PIPELINE_CACHE_BUCKET env var AND
    prefix starts with '{PIPELINE_CACHE_PREFIX}'.

    Uses get_pipeline_cache_config() internally to read environment variables.
    """
    pipeline_cache_bucket, pipeline_cache_prefix = get_pipeline_cache_config()

    return (
        bucket == pipeline_cache_bucket
        and prefix.startswith(pipeline_cache_prefix)
    )
