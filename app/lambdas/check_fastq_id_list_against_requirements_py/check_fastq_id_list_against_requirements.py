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

    satisfied_requirements, unsatisfied_requirements = check_fastq_list_against_requirements_list(
        fastq_list=fastq_obj_list,
        requirements=requirements,
        is_unarchiving_allowed=is_unarchiving_allowed
    )

    fastq_id_list_with_missing_requirements = []

    if len(unsatisfied_requirements) > 0:
        for fastq_obj_iter in fastq_obj_list:
            satisfied_requirements_iter, unsatisfied_requirements_iter = check_fastq_list_against_requirements_list(
                fastq_list=[fastq_obj_iter],
                requirements=requirements,
                is_unarchiving_allowed=is_unarchiving_allowed
            )
            if len(unsatisfied_requirements_iter) > 0:
                fastq_id_list_with_missing_requirements.append(fastq_obj_iter['id'])

    # Return the results
    return {
        "fastqIdListWithMissingRequirements": fastq_id_list_with_missing_requirements,
        "hasAllRequirements": (True if len(unsatisfied_requirements) == 0 else False),
    }


# if __name__ == "__main__":
#     import json
#     from os import environ
#
#     environ['AWS_PROFILE'] = 'umccr-development'
#     environ['HOSTNAME_SSM_PARAMETER_NAME'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['BYOB_BUCKET_PREFIX'] = 's3://pipeline-dev-cache-503977275616-ap-southeast-2/byob-icav2/development/'
#
#     print(json.dumps(
#         handler({
#             "fastqIdList": [
#                 "fqr.01JQ3BEKYHYB1CBDK92X10CF3H"
#             ],
#             "requirements": {
#                 "hasQc": True,
#                 "hasFingerprint": True,
#                 "hasActiveReadSet": True
#             },
#             "isUnarchivingAllowed": True
#         }, None),
#         indent=4
#     ))
#
#     # {
#     #     "hasAllRequirements": true
#     # }
