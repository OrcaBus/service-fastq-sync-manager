#!/usr/bin/env python3

"""
Check running jobs for fastq id list

Iterate over a list of fastq ids, check the fastq unarchiver and the fastq manager jobs list.

We return a 'true' if any of the fastq ids have jobs running, as this means that the task token
is still active.

Otherwise we return 'false'.
"""

# Standard library imports
from typing import List, Literal, Dict

# Layer imports
# Workflow
from orcabus_api_tools.workflow import list_workflow_runs, get_workflow_run
# Fastq
from orcabus_api_tools.fastq import (
    get_fastq_jobs as get_fastq_manager_jobs,
    get_fastq
)
from orcabus_api_tools.fastq_unarchiving import get_job_list_for_fastq as get_unarchiving_job_list_for_fastq

# Globals
ACTIVE_JOB_STATUS_LIST_TYPE = Literal['PENDING', 'RUNNING']
ACTIVE_JOB_STATUS_LIST: List[ACTIVE_JOB_STATUS_LIST_TYPE] = ['PENDING', 'RUNNING']

BCLCONVERT_WORKFLOW_NAME = 'bclconvert'
BSSH_TO_AWS_S3_WORKFLOW_NAME = 'bssh-to-aws-s3'
ACTIVE_WORKFLOW_STATUS_LIST = [
    'DRAFT',
    'READY',
    'RUNNING',
    'SUCCEEDED'
]


def handler(event, context) -> Dict[str, bool]:
    """
    Check running jobs for fastq id list
    :param event:
    :param context:
    :return:
    """

    # Get fastq id list
    fastq_id_list: List[str] = event['fastqIdList']

    # Iterate over fastq ids
    # If any of them have jobs running, return true immediately
    for fastq_id in fastq_id_list:
        # Check fastq manager jobs
        if len(
                list(filter(
                    lambda job: job['status'] in ACTIVE_JOB_STATUS_LIST,
                    get_fastq_manager_jobs(fastq_id=fastq_id)
                ))
        ) > 0:
            return {
                "jobsRunning": True
            }
        # Check fastq unarchiver jobs
        for active_status in ACTIVE_JOB_STATUS_LIST:
            if len(get_unarchiving_job_list_for_fastq(
                    fastq_id=fastq_id,
                    job_status=active_status
            )) > 0:
                return {
                    "jobsRunning": True
                }

        # Get the library id of the fastq
        library_id = get_fastq(fastq_id)['library']['libraryId']

        # Check workflow runs for fastq unarchiver associated with this library
        for status_iter in ACTIVE_WORKFLOW_STATUS_LIST:
            # Check bclconvert workflow runs
            bclconvert_workflow_runs = list_workflow_runs(
                workflow_name=BCLCONVERT_WORKFLOW_NAME,
                current_status=status_iter,
            )
            bssh_to_aws_s3_workflow_runs = list_workflow_runs(
                workflow_name=BSSH_TO_AWS_S3_WORKFLOW_NAME,
                current_status=status_iter,
            )

            # Check if the library is associated with any of the workflow runs
            for workflow_run in (bclconvert_workflow_runs + bssh_to_aws_s3_workflow_runs):
                library_id_list = list(map(
                    lambda library_iter_: library_iter_['libraryId'],
                    get_workflow_run(workflow_run['orcabusId'])['libraries']
                ))

                if any(library_id == library_id_iter for library_id_iter in library_id_list):
                    return {
                        "jobsRunning": True
                    }

    # If we get here, no jobs are running
    return {
        "jobsRunning": False
    }
