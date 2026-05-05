import * as path from 'path';
import { Duration } from 'aws-cdk-lib';

// Dir constants
export const APP_ROOT = path.join(__dirname, '../../', 'app');
export const LAMBDA_ROOT = path.join(APP_ROOT, 'lambdas');
export const STEP_FUNCTIONS_ROOT = path.join(APP_ROOT, 'step-functions-templates');
export const LAYERS_ROOT = path.join(APP_ROOT, 'layers');

// Table constants
export const FASTQ_SYNC_TASK_TOKEN_TABLE_NAME = 'FastqSyncTaskTokenTable';

// Event constants
export const FASTQ_SYNC_EVENT_DETAIL_TYPE = 'FastqSync';

// External events to listen to
export const FASTQ_STATE_CHANGE_EVENT_DETAIL_TYPE = 'FastqStateChange';
export const FASTQ_MANAGER_EVENT_SOURCE = 'orcabus.fastqmanager';

// Events for unarchiving jobs
export const FASTQ_UNARCHIVING_JOB_EVENT_DETAIL_TYPE = 'FastqUnarchivingJobStateChange';
export const FASTQ_UNARCHIVING_MANAGER_EVENT_SOURCE = 'orcabus.fastqunarchiving';

// Event rule constants
export const HEART_BEAT_SCHEDULER_RULE_NAME = 'heartbeatFastqSyncJobsScheduler';
export const DEFAULT_HEART_BEAT_INTERVAL = Duration.seconds(900); // 15 minutes in seconds

// Slack Topic Name
export const DEFAULT_SLACK_TOPIC_NAME = 'AwsChatBotTopic';

// Sqs Queue Name
export const DEFAULT_SQS_QUEUE_NAME = 'FastqSyncRequestQueue';
export const DEFAULT_QUEUE_TIMEOUT = Duration.seconds(360);
export const DEFAULT_MAX_FASTQ_SYNC_REQUEST_CONCURRENCY = 20;

// Step functions constants
export const STACK_PREFIX = 'fastq-sync';
