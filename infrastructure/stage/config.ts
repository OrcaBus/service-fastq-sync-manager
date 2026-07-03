import { StatefulApplicationConfig, StatelessApplicationConfig } from './interfaces';
import {
  DEFAULT_SLACK_TOPIC_NAME,
  DEFAULT_SQS_QUEUE_NAME,
  FASTQ_SYNC_TASK_TOKEN_TABLE_NAME,
  TEST_DATA_BUCKET,
  TEST_DATA_PREFIX,
} from './constants';
import { EVENT_BUS_NAME } from '@orcabus/platform-cdk-constructs/shared-config/event-bridge';
import { StageName } from '@orcabus/platform-cdk-constructs/shared-config/accounts';
import { PIPELINE_CACHE_BUCKET } from '@orcabus/platform-cdk-constructs/shared-config/s3';

/**
 * Mapping from deployment stage to BYOB environment identifier.
 */
const PIPELINE_CACHE_PREFIX: Record<StageName, string> = {
  BETA: 'byob-icav2/development/',
  GAMMA: 'byob-icav2/staging/',
  PROD: 'byob-icav2/production/',
};

export const getStatefulApplicationProps = (): StatefulApplicationConfig => {
  return {
    // Dynamodb stuff
    tableName: FASTQ_SYNC_TASK_TOKEN_TABLE_NAME,

    // Sqs Stuff
    sqsQueueName: DEFAULT_SQS_QUEUE_NAME,

    // Slack topic name
    slackTopicName: DEFAULT_SLACK_TOPIC_NAME,
  };
};

export const getStatelessApplicationProps = (stage: StageName): StatelessApplicationConfig => {
  return {
    // Event Bus
    eventBusName: EVENT_BUS_NAME,

    // Dynamodb
    tableName: FASTQ_SYNC_TASK_TOKEN_TABLE_NAME,

    // Sqs event sourcing
    sqsQueueName: DEFAULT_SQS_QUEUE_NAME,

    // Pipeline cache configuration
    pipelineCacheBucket: PIPELINE_CACHE_BUCKET[stage],
    pipelineCachePrefix: PIPELINE_CACHE_PREFIX[stage],

    // Test data configuration
    testDataBucket: TEST_DATA_BUCKET,
    testDataPrefix: TEST_DATA_PREFIX,
  };
};
