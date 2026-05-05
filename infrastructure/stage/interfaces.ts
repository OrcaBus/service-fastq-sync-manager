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
}
