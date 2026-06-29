# Product Overview

The Fastq Sync Manager is a service within the OrcaBus platform that enables workflow orchestration services to pause execution until primary sequencing data (FASTQ files) meets specific readiness conditions.

## Core Purpose

Other step functions across the platform can "hang" at a point in their execution, waiting for FASTQ data to reach a required state before proceeding. Supported conditions include:

- FASTQ restored from archive
- FASTQ contains a valid read set
- FASTQ contains QC data

## Event-Driven Architecture

The service consumes events via AWS EventBridge and processes them through Step Functions and Lambda handlers. It uses a task-token callback pattern — callers send a task token with their sync request, and the service sends a callback when the data conditions are met.

## Key Concepts

- **Task Token**: An AWS Step Functions token provided by the caller, used to resume the caller's execution once conditions are satisfied.
- **Fastq ID (`fqr.*`)**: Identifier for an individual FASTQ record.
- **Fastq Set ID (`fqs.*`)**: Identifier for a group of related FASTQ records.
- **Requirements**: A set of boolean conditions (e.g., `hasActiveReadSet`) that must be true before the callback fires.
- **Force Unarchiving**: Optional flag to trigger restoration from Glacier/archive storage.

## Event Sources

| DetailType                       | Source                          |
| -------------------------------- | ------------------------------- |
| `FastqSync`                      | Any (sync request from callers) |
| `FastqStateChange`               | `orcabus.fastqmanager`          |
| `FastqUnarchivingJobStateChange` | `orcabus.fastqunarchiving`      |

## Deployment

Fully automated CI/CD via AWS CodePipeline. All merges to `main` are deployed through beta → gamma → prod stages.
