import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { buildAllLambdas, buildFastqSyncToolsLayer } from './lambdas';
import { buildAllStepFunctions } from './step-functions';
import { StatelessApplicationConfig } from './interfaces';

import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import { buildAllEventRules } from './event-rules';
import { buildAllEventBridgeTargets } from './event-targets';
import { IQueue } from 'aws-cdk-lib/aws-sqs';

export type StatelessApplicationStackProps = cdk.StackProps & StatelessApplicationConfig;

export class StatelessApplicationStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: StatelessApplicationStackProps) {
    super(scope, id, props);

    /**
     * Define your stack to be deployed in stages here
     */

    // Get the event bus from the props
    const eventBus = events.EventBus.fromEventBusName(this, 'event-bus', props.eventBusName);

    // Get the table from the props
    const tableObj = dynamodb.TableV2.fromTableName(this, 'table', props.tableName);

    // Get the internal SQS Queue from props
    const sqsQueue: IQueue = sqs.Queue.fromQueueArn(
      this,
      props.sqsQueueName,
      `arn:aws:sqs:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:${props.sqsQueueName}`
    );

    // Build lambda layer
    const fastqSyncToolsLayer = buildFastqSyncToolsLayer(this);

    // Build the lambda functions
    const lambdaObjects = buildAllLambdas(this, {
      fastqSyncLayer: fastqSyncToolsLayer,
      sqsQueue: sqsQueue,
      initialiseTaskTokenForFastqIdListSfnName: 'initialiseTaskTokenForFastqIdList',
      ...props
    });

    // Build the state machines
    const stateMachines = buildAllStepFunctions(this, {
      lambdaObjects: lambdaObjects,
      eventBus: eventBus,
      tableObj: tableObj,
      sqsQueue: sqsQueue,
    });

    // Build the event rules
    const eventRules = buildAllEventRules(this, {
      eventBus: eventBus,
    });

    // Build the event targets
    buildAllEventBridgeTargets({
      eventBridgeRuleObjects: eventRules,
      stepFunctionObjects: stateMachines,
    });
  }
}
