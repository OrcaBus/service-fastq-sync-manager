import * as cdk from 'aws-cdk-lib';
import { SqsQueueConstructProps } from './interfaces';
import { Queue } from 'aws-cdk-lib/aws-sqs';
import { Construct } from 'constructs';
import { MonitoredQueue } from 'sqs-dlq-monitoring';

// Get the topic ARN from the topic name
export function getTopicArnFromTopicName(topicName: string): string {
  return `arn:aws:sns:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:${topicName}`;
}

// Create the INPUT SQS queue that will receive the ICA events
// This should have a DLQ and be monitored via CloudWatch alarm and Slack notifications
export function createMonitoredQueue(scope: Construct, props: SqsQueueConstructProps): Queue {
  // Note: the construct MonitoredQueue demands a "Topic" construct as it usually modifies the topic adding subscriptions.
  // However, our use case, as we don't add any additional subscriptions, does not require topic modification, so we can pass on an "ITopic" as "Topic".
  const mq = new MonitoredQueue(scope, props.queueName, {
    queueProps: {
      queueName: props.queueName,
      enforceSSL: true,
      visibilityTimeout: props.queueVizTimeout,
      receiveMessageWaitTime: props.receiveMessageWaitTime,
    },
    dlqProps: {
      queueName: props.queueName + '-dlq',
      enforceSSL: true,
      visibilityTimeout: props.queueVizTimeout,
    },
    messageThreshold: props.dlqMessageThreshold,
    topic: props.slackTopic,
  });
  return mq.queue;
}
