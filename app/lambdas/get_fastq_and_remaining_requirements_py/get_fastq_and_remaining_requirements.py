#!/usr/bin/env python3

"""
Get the fastq list row and requirements for a given fastq id

Inputs:
  * fastqId
  * requirements

Outputs:
* fastqObj
* satisfiedRequirements
* unsatisfiedRequirements

"""
from typing import List

from orcabus_api_tools.fastq import get_fastq
from fastq_sync_tools import check_fastq_against_requirements_list, REQUIREMENT


def handler(event, context):
    """
    Lambda handler function
    """
    fastq_id: str = event.get("fastqId")
    requirements: List[REQUIREMENT] = event.get("requirements", [])
    is_unarchiving_allowed: bool = event.get("isUnarchivingAllowed", False)

    if not fastq_id:
        raise ValueError("fastqId is required")

    fastq_obj = get_fastq(fastq_id, includeS3Details=True)

    satisfied_requirements, unsatisfied_requirements = (
        check_fastq_against_requirements_list(
            fastq_obj=fastq_obj,
            requirements=requirements,
            is_unarchiving_allowed=is_unarchiving_allowed
        )
    )

    return {
        "fastqObj": fastq_obj,
        "satisfiedRequirements": satisfied_requirements,
        "unsatisfiedRequirements": unsatisfied_requirements,
    }
