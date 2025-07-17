import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { buildAllLambdas, buildFastqSyncToolsLayer } from './lambdas';
import { buildAllStepFunctions } from './step-functions';
import { StatelessApplicationConfig } from './interfaces';

import * as events from 'aws-cdk-lib/aws-events';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { buildAllEventRules } from './event-rules';
import { buildAllEventBridgeTargets } from './event-targets';

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

    // Build lambda layer
    const fastqSyncToolsLayer = buildFastqSyncToolsLayer(this);

    // Build the lambda functions
    const lambdaObjects = buildAllLambdas(this, {
      fastqSyncLayer: fastqSyncToolsLayer,
      pipelineCacheBucketName: props.pipelineCacheBucketName,
      pipelineCacheKeyPrefix: props.pipelineCacheKeyPrefix,
    });

    // Build the state machines
    const stateMachines = buildAllStepFunctions(this, {
      lambdaObjects: lambdaObjects,
      eventBus: eventBus,
      tableObj: tableObj,
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
