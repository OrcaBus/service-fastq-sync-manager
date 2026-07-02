/*
Interfaces for the application stacks
 */

export interface StatefulApplicationConfig {
  /* Dynamodb */
  tableName: string;

  /* Sqs Stuff */
  sqsQueueName: string;

  /* Notification stuff */
  slackTopicName: string;
}

export interface StatelessApplicationConfig {
  // Event Stuff
  eventBusName: string;

  // Dynamodb stuff
  tableName: string;

  // Sqs stuff
  sqsQueueName: string;

  // Pipeline cache configuration
  pipelineCacheBucket: string;
  pipelineCachePrefix: string;

  // Test data configuration
  testDataBucket: string;
  testDataPrefix: string;
}
