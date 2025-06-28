#!/usr/bin/env python

from typing import Literal

ACTIVE_STORAGE_CLASSES = Literal[
    "Standard",
    "StandardIa",
    "IntelligentTiering",
    "GlacierIr",
    "Glacier",
    "DeepArchive",
]

BYOB_BUCKET_PREFIX_ENV_VAR = "BYOB_BUCKET_PREFIX"

REQUIREMENT = Literal[
    "hasActiveReadSet",
    "hasQc",
    "hasFingerprint",
    "hasFileCompressionInformation",
]
