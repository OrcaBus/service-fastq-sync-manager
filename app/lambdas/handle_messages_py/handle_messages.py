#!/usr/bin/env python3

"""
Throttle messages coming through from SQS

We may have a lot of requests come through at once, we run a maximum of 10 lambdas
simultaneously, each of which we assume will only take a few seconds to complete

We run the step functions asynchonously with a callback id.

We let the step functions handle the task tokens
"""

# Standard library imports
import json
from os import environ
import boto3
import typing
from typing import Dict, Any

# Durable context imports
from aws_durable_execution_sdk_python import (
    DurableContext,
    durable_execution,
)
from aws_durable_execution_sdk_python.config import (
    Duration, WaitForCallbackConfig
)

from aws_durable_execution_sdk_python.retries import create_retry_strategy
from aws_durable_execution_sdk_python.types import WaitForCallbackContext

if typing.TYPE_CHECKING:
    from mypy_boto3_stepfunctions.client import SFNClient


# Globals
INITIALISE_TASK_TOKEN_FOR_FASTQ_ID_LIST_SFN_ARN_ENV_VAR = "INITIALISE_TASK_TOKEN_FOR_FASTQ_ID_LIST_SFN_ARN"


def get_sfn_client() -> 'SFNClient':
    return boto3.client('stepfunctions')


def run_execution(sfn_input: Dict[str, Any], context: DurableContext) -> None:
    # Define the wrapper function
    def submitter(callback_id: str, callback_context: WaitForCallbackContext):
        callback_context.logger.info("Submitting fastq sync request job")
        # Step 2: Launch the fastq sync job (asynchronously)
        sfn_object = get_sfn_client().start_execution(
            stateMachineArn=environ[INITIALISE_TASK_TOKEN_FOR_FASTQ_ID_LIST_SFN_ARN_ENV_VAR],
            input=json.dumps({
                **sfn_input,
                "callbackId": callback_id,
            }),
        )
        callback_context.logger.info(f"Submitting fastq sync request job as {sfn_object['executionArn']}")

    # Step 3: Wait here for the callback to be invoked
    context.wait_for_callback(
        submitter=submitter,
        name=None,
        config=WaitForCallbackConfig(
            timeout=Duration.from_minutes(15),
            retry_strategy=create_retry_strategy(
                config=None
            )
        ),
    )

@durable_execution
def handler(event, context: DurableContext):
    """
    Expect the following inputs from the event object:
      * inputs
      * engineParameters
      * tags

    :param event:
    :param context:
    :return:
    """

    # Not sure what this will look like from the sqs event source
    for record in event.get("Records", []):
        record_body = json.loads(record.get("body", "{}"))
        # Check if the event contains the required keys
        required_keys = ['payload']
        for key in required_keys:
            if key not in record_body:
                raise ValueError(f"Missing required key: {key}")

        # Run the durable execution callback configuration
        run_execution(record_body, context)
