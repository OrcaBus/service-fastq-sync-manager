#!/usr/bin/env python3

"""
Check fastq id list against the requirements

Takes in the inputs:
  * fastqIdList: list of fastq ids
  * requirements: list of requirements to check against
  * isUnarchivingAllowed: boolean indicating if unarchiving is allowed

And outputs the following:

* hasAllRequirements: boolean

"""

# Standard imports
from typing import List
from requests import HTTPError

from fastq_sync_tools.utils.utils import check_fastq_set_against_requirements_list
# Layer imports
from orcabus_api_tools.fastq import get_fastq, get_fastq_set
from fastq_sync_tools import check_fastq_list_against_requirements_list
from fastq_sync_tools.utils.globals import FASTQ_SET_REQUIREMENT


def handler(event, context):
    """
    Check the fastq id list against the requirements set
    :param event:
    :param context:
    :return:
    """
    fastq_set_id: str = event.get("fastqSetId", [])
    requirements: List[FASTQ_SET_REQUIREMENT] = event.get("requirements", [])
    is_unarchiving_allowed: bool = event.get("isUnarchivingAllowed", False)
    wait_for_bam: bool = event.get("waitForBam", False)

    # Get fastq set
    try:
        fastq_set_obj = get_fastq_set(
            fastq_set_id,
            includeS3Details=True
        )
    except HTTPError:
        # Return the results
        return {
            "hasAllRequirements": False,
        }

    satisfied_requirements, unsatisfied_requirements = check_fastq_set_against_requirements_list(
        fastq_set_obj=fastq_set_obj,
        requirements=requirements,
    )

    # Return the results
    return {
        "hasAllRequirements": (True if len(unsatisfied_requirements) == 0 else False),
    }
