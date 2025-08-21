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

REQUIREMENT = Literal[
    "hasActiveReadSet",
    "hasQc",
    "hasFingerprint",
    "hasFileCompressionInformation",
    "hasReadCountInformation",
]
