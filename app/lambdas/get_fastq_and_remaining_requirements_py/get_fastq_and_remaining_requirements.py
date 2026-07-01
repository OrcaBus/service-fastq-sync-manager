#!/usr/bin/env python3

"""
Get the fastq list row and requirements for a given fastq id

Inputs:
  * fastqId
  * requirements
  * hasActiveReadSetContext (optional)

Outputs:
* fastqObj
* satisfiedRequirements
* unsatisfiedRequirements

"""

# Standard imports
from typing import Dict, List, Optional

# Orcabus imports
from orcabus_api_tools.fastq import get_fastq

# Local layer imports
from fastq_sync_tools import (
    check_fastq_against_requirements_list,
    ContextNotEligibleError,
    REQUIREMENT,
)


def handler(event, context):
    """
    Lambda handler function
    """
    fastq_id: str = event.get("fastqId")
    requirements: List[REQUIREMENT] = event.get("requirements", [])
    is_unarchiving_allowed: bool = event.get("isUnarchivingAllowed", False)
    has_active_readset_context: Optional[Dict[str, str]] = event.get("hasActiveReadSetContext", None)

    if not fastq_id:
        raise ValueError("fastqId is required")

    fastq_obj = get_fastq(fastq_id, includeS3Details=True)

    try:
        satisfied_requirements, unsatisfied_requirements = (
            check_fastq_against_requirements_list(
                fastq_obj=fastq_obj,
                requirements=requirements,
                is_unarchiving_allowed=is_unarchiving_allowed,
                has_active_readset_context=has_active_readset_context,
            )
        )
    except ContextNotEligibleError:
        raise

    return {
        "fastqObj": fastq_obj,
        "satisfiedRequirements": satisfied_requirements,
        "unsatisfiedRequirements": unsatisfied_requirements,
    }
