#!/usr/bin/env python3

"""
Given a requirement item and a fastq list row id, launch a job against the requirement item

For qc, fingerprint or compression, we use the fastq api endpoint,
For unarchiving we use the fastq unarchiving endpoint

The requirementType input will be one of the following:

ACTIVE_READSET
QC
FINGERPRINT
COMPRESSION_METADATA

"""

# Orcabus API tools
from orcabus_api_tools.fastq import (
    get_fastq
)

# Layer imports
from fastq_sync_tools import (
    REQUIREMENT,
    run_fastq_job,
    run_fastq_unarchiving_job,
    check_fastq_unarchiving_job,
    check_fastq_job
)


def handler(event, context):
    """
    Get the requirement type and launch the job
    :param event:
    :param context:
    :return:
    """
    # Get inputs
    fastq_id = event['fastqId']
    requirement_type: REQUIREMENT = event['requirementType']

    # Get the fastq list row as an object
    fastq_obj = get_fastq(fastq_id, includeS3Details=True)

    # Launch unarchiving job
    if requirement_type == "hasActiveReadSet" and check_fastq_unarchiving_job(fastq_id):
        run_fastq_unarchiving_job(
            fastq_obj
        )

    # Run internal jobs
    if check_fastq_job(fastq_id, "QC") and requirement_type == "hasQc":
        run_fastq_job(fastq_obj, "QC")

    if check_fastq_job(fastq_id, "NTSM") and requirement_type == "hasFingerprint":
        run_fastq_job(fastq_obj, "NTSM")

    if check_fastq_job(fastq_id, "FILE_COMPRESSION") and requirement_type == "hasFileCompressionInformation":
        run_fastq_job(fastq_obj, "FILE_COMPRESSION")



# if __name__ == "__main__":
#     import json
#     from os import environ
#     environ['AWS_PROFILE'] = 'umccr-production'
#     environ['AWS_REGION'] = 'ap-southeast-2'
#     environ['HOSTNAME_SSM_PARAMETER_NAME'] = '/hosted_zone/umccr/name'
#     environ['ORCABUS_TOKEN_SECRET_ID'] = 'orcabus/token-service-jwt'
#     environ['BYOB_BUCKET_PREFIX'] = 's3://pipeline-prod-cache-503977275616-ap-southeast-2/byob-icav2/production/'
#     print(json.dumps(
#         handler(
#             {
#                 "fastqId": "fqr.01JN25XG75K54W8YF0J9MXVZKA",
#                 "requirementType": "hasActiveReadSet"
#             },
#             None
#         ),
#         indent=4
#     ))
