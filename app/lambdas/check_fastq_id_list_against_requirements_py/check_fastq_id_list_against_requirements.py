#!/usr/bin/env python3

"""
Check fastq id list against the requirements

Takes in the inputs:
  * fastqIdList: list of fastq ids
  * requirements: dict of requirement names to boolean or context object values
  * isUnarchivingAllowed: boolean indicating if unarchiving is allowed

And outputs the following:

* hasAllRequirements: boolean
* fastqIdListWithMissingRequirements: list of fastq ids that are missing requirements

"""

# Standard imports
from typing import Dict, List, Optional, Union, cast
from requests import HTTPError

# Layer imports
from orcabus_api_tools.fastq import get_fastq
from fastq_sync_tools import (
    check_fastq_list_against_requirements_list,
    validate_has_active_readset_input,
    REQUIREMENT,
)


def handler(event, context):
    """
    Check the fastq id list against the requirements set
    :param event:
    :param context:
    :return:
    """
    fastq_id_list: List[str] = event.get("fastqIdList", [])
    requirements_dict: Dict[REQUIREMENT, Union[bool, Dict[str, str]]] = event.get("requirements", {})
    is_unarchiving_allowed: bool = event.get("isUnarchivingAllowed", False)

    # Parse requirements dict into a List[REQUIREMENT] and extract context if present
    requirements: List[REQUIREMENT] = []
    has_active_readset_context: Optional[Dict[str, str]] = None

    for req_name, req_value in requirements_dict.items():
        if req_name == "hasActiveReadSet":
            # Validate and parse hasActiveReadSet value
            try:
                is_context_aware, bucket, prefix = validate_has_active_readset_input(req_value)
            except ValueError as e:
                raise ValueError(
                    f"Invalid hasActiveReadSet requirement value: {e}"
                ) from e

            # Include hasActiveReadSet in the requirements list
            requirements.append("hasActiveReadSet")

            # If context-aware, extract the context object
            if is_context_aware:
                has_active_readset_context = {
                    "bucket": cast(str, bucket),
                    "prefix": cast(str, prefix),
                }
        else:
            # For other requirements, include if value is truthy
            if req_value:
                requirements.append(req_name)

    # Get fastqs
    try:
        fastq_obj_list = list(map(
            lambda fastq_id_iter_: get_fastq(fastq_id_iter_, includeS3Details=True),
            fastq_id_list
        ))
    except HTTPError:
        # Return the results
        return {
            "fastqIdListWithMissingRequirements": fastq_id_list,
            "hasAllRequirements": False,
        }

    # Check requirements for the full list — ContextNotEligibleError propagates
    satisfied_requirements, unsatisfied_requirements = check_fastq_list_against_requirements_list(
        fastq_list=fastq_obj_list,
        requirements=requirements,
        is_unarchiving_allowed=is_unarchiving_allowed,
        has_active_readset_context=has_active_readset_context,
    )

    fastq_id_list_with_missing_requirements = []

    if len(unsatisfied_requirements) > 0:
        for fastq_obj_iter in fastq_obj_list:
            satisfied_requirements_iter, unsatisfied_requirements_iter = check_fastq_list_against_requirements_list(
                fastq_list=[fastq_obj_iter],
                requirements=requirements,
                is_unarchiving_allowed=is_unarchiving_allowed,
                has_active_readset_context=has_active_readset_context,
            )
            if len(unsatisfied_requirements_iter) > 0:
                fastq_id_list_with_missing_requirements.append(fastq_obj_iter['id'])

    # Return the results
    return {
        "fastqIdListWithMissingRequirements": fastq_id_list_with_missing_requirements,
        "hasAllRequirements": (True if len(unsatisfied_requirements) == 0 else False),
    }
