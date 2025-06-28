#!/usr/bin/env python3

"""
Given a list of fastq set ids, convert to a list of fastq ids


Inputs:
  * fastqSetIdList

Outputs:
  * fastqIdList
"""

from functools import reduce
from operator import concat
from typing import List

from orcabus_api_tools.fastq import get_fastq_set
from orcabus_api_tools.fastq.models import FastqSet


def handler(event, context):
    """
    Lambda handler function
    """
    # Get the fastq set id list from the event
    fastq_set_id_list: List[str] = event.get("fastqSetIdList", [])

    # Get the list of fastq sets as objects
    fastq_set_obj_list: List[FastqSet] = list(map(
        get_fastq_set,
        fastq_set_id_list
    ))

    fastq_id_list: List[str] = list(reduce(
        concat,
        list(map(
            lambda fastq_set_iter: list(map(
                lambda fastq: fastq.get("id", None),
                fastq_set_iter.get("fastqSet", [])
            )),
            fastq_set_obj_list
        ))
    ))

    return {
        "fastqIdList": fastq_id_list
    }
