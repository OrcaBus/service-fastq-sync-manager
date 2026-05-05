import { StatefulApplicationConfig, StatelessApplicationConfig } from './interfaces';
import {
  DEFAULT_SLACK_TOPIC_NAME,
  DEFAULT_SQS_QUEUE_NAME,
  FASTQ_SYNC_TASK_TOKEN_TABLE_NAME,
} from './constants';
import { EVENT_BUS_NAME } from '@orcabus/platform-cdk-constructs/shared-config/event-bridge';

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

export const getStatelessApplicationProps = (): StatelessApplicationConfig => {
  return {
    // Event Bus
    eventBusName: EVENT_BUS_NAME,

    // Dynamodb
    tableName: FASTQ_SYNC_TASK_TOKEN_TABLE_NAME,

    // Sqs event sourcing
    sqsQueueName: DEFAULT_SQS_QUEUE_NAME,
  };
};
