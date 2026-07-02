#!/usr/bin/env python3

"""
Custom exceptions for the fastq sync tools layer.
"""


class ContextNotEligibleError(Exception):
    """Raised when hasActiveReadSet context doesn't match allowed pipeline-cache bucket."""

    def __init__(self, bucket: str, prefix: str):
        self.bucket = bucket
        self.prefix = prefix
        super().__init__(
            f"FASTQ is not available in the requested context "
            f"(bucket={bucket}, prefix={prefix}) and the context "
            f"is not eligible for automatic resolution."
        )
