#!/usr/bin/env python3

"""
Bunch of useful helper functions for lambdas in the fastq sync service
"""


from os import environ
from typing import Optional, List, Tuple

from orcabus_api_tools.fastq import (
    get_fastq_jobs,
    run_qc_stats,
    run_file_compression_stats,
    run_ntsm, run_read_count_stats
)

from orcabus_api_tools.fastq.models import (
    JobStatus, Job, JobType,
    FastqListRow
)

from orcabus_api_tools.fastq_unarchiving import (
    create_job as create_unarchiving_job,
    get_job_list_for_fastq
)

from orcabus_api_tools.fastq_unarchiving.models import (
    Job as UnarchivingJob,
    JobStatus as UnarchivingJobStatus
)

from .globals import (
    BYOB_BUCKET_PREFIX_ENV_VAR,
    REQUIREMENT,
    ACTIVE_STORAGE_CLASSES
)


def has_active_readset(fastq_obj: 'FastqListRow') -> bool:
    if fastq_obj['readSet'] is None:
        return False

    readset_objects = list(filter(
        lambda readset_iter_: readset_iter_ is not None,
        [fastq_obj['readSet']['r1'], fastq_obj['readSet']['r2']]
    ))

    for readset_object in readset_objects:
        # If the storage class is not in the active storage classes or
        # the s3 uri does not start with the bucket prefix
        # then return False
        if (
                (readset_object['storageClass'] not in ACTIVE_STORAGE_CLASSES)
                or
                (not readset_object['s3Uri'].startswith(environ[BYOB_BUCKET_PREFIX_ENV_VAR]))
        ):
            return False

    return True


def has_qc(fastq_obj: FastqListRow) -> bool:
    return fastq_obj['qc'] is not None


def has_fingerprint(fastq_obj: FastqListRow) -> bool:
    return fastq_obj['ntsm'] is not None


def has_compression_metadata(fastq_obj: FastqListRow) -> bool:
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
                                    JobType(job_iter_['jobType']) == job_type
                            ) and
                            (
                                    JobStatus(job_iter_['status']) in [JobStatus.PENDING, JobStatus.RUNNING]
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
                len(get_job_list_for_fastq(fastq_id, UnarchivingJobStatus.PENDING)) == 0
            ) and
            (
                len(get_job_list_for_fastq(fastq_id, UnarchivingJobStatus.RUNNING)) == 0
            )
    )


def run_fastq_job(fastq: FastqListRow, job_type: JobType) -> Optional[Job]:
    """
    Run a job for a fastq
    :param fastq:
    :param job_type:
    :return:
    """
    # Check that the fastq list row has an active read set
    if not has_active_readset(fastq):
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


def run_fastq_unarchiving_job(fastq: FastqListRow) -> Optional[UnarchivingJob]:
    create_unarchiving_job(
        fastq_ids=[
            fastq['id']
        ],
        job_type='S3_UNARCHIVING'
    )


def check_fastq_against_requirements_list(
        fastq_obj: FastqListRow,
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
            if has_compression_metadata(fastq_obj):
                satisfied_requirements.append(requirement_iter_)
            else:
                unsatisfied_requirements.append(requirement_iter_)


    return satisfied_requirements, unsatisfied_requirements


def check_fastq_list_against_requirements_list(
        fastq_list: List[FastqListRow],
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
