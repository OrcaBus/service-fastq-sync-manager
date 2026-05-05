import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { buildTaskTokenTable } from './dynamodb';
import { StatefulApplicationConfig } from './interfaces';
import { createMonitoredQueue, getTopicArnFromTopicName } from './sqs';
import { Topic } from 'aws-cdk-lib/aws-sns';
import { Duration } from 'aws-cdk-lib';
import { DEFAULT_QUEUE_TIMEOUT } from './constants';

export type StatefulApplicationStackProps = cdk.StackProps & StatefulApplicationConfig;

export class StatefulApplicationStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: StatefulApplicationStackProps) {
    super(scope, id, props);

    /**
     * Define your stack to be deployed in stages here
     *
     */

    // Build the dynamodb tables
    buildTaskTokenTable(this, {
      tableName: props.tableName,
    });

    // Get the slack topic
    const slackTopic: Topic = Topic.fromTopicArn(
      this,
      'SlackTopic',
      getTopicArnFromTopicName(props.slackTopicName)
    ) as Topic;

    // Buffer to fastq sync requests
    createMonitoredQueue(this, {
      dlqMessageThreshold: 1,
      queueName: props.sqsQueueName,
      queueVizTimeout: DEFAULT_QUEUE_TIMEOUT,
      slackTopic: slackTopic,
      receiveMessageWaitTime: Duration.seconds(20),
    });
  }
}
