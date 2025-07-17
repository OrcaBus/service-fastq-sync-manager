#!/usr/bin/env python

from typing import Literal, List

ACTIVE_STORAGE_CLASSES_TYPE = Literal[
    "Standard",
    "StandardIa",
    "IntelligentTiering",
    "GlacierIr",
    # "Glacier",
    # "DeepArchive",
]

ACTIVE_STORAGE_CLASSES: List[ACTIVE_STORAGE_CLASSES_TYPE] = list(ACTIVE_STORAGE_CLASSES_TYPE.__args__)

BYOB_BUCKET_PREFIX_ENV_VAR = "BYOB_BUCKET_PREFIX"

REQUIREMENT = Literal[
    "hasActiveReadSet",
    "hasQc",
    "hasFingerprint",
    "hasFileCompressionInformation",
    "hasReadCountInformation",
]
