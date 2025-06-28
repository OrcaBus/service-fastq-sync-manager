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
from typing import List

from orcabus_api_tools.fastq import get_fastq
from fastq_sync_tools import check_fastq_list_against_requirements_list
from fastq_sync_tools.utils.globals import REQUIREMENT


def handler(event, context):
    """
    Check the fastq id list against the requirements set
    :param event:
    :param context:
    :return:
    """

    fastq_id_list: List[str] = event.get("fastqIdList", [])
    requirements: List[REQUIREMENT] = event.get("requirements", [])
    is_unarchiving_allowed: bool = event.get("isUnarchivingAllowed", False)

    # Get fastqs
    fastq_obj_list = list(map(
        lambda fastq_id_iter_: get_fastq(fastq_id_iter_, includeS3Details=True),
        fastq_id_list
    ))

    has_all_requirements = check_fastq_list_against_requirements_list(
        fastq_list=fastq_obj_list,
        requirements=requirements,
        is_unarchiving_allowed=is_unarchiving_allowed
    )

    return {
        "hasAllRequirements": has_all_requirements
    }
