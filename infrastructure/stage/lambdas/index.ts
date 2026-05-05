import { NagSuppressions } from 'cdk-nag';
import { Duration } from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import { Construct } from 'constructs';
import {
  BuildAllLambdaProps,
  lambdaNameList,
  LambdaObject,
  LambdaProps,
  lambdaRequirementsMap,
} from './interfaces';
import * as path from 'path';
import * as cdk from 'aws-cdk-lib';
import { camelCaseToSnakeCase } from '../utils';
import { getPythonUvDockerImage, PythonUvFunction } from '@orcabus/platform-cdk-constructs/lambda';
import {
  DEFAULT_MAX_FASTQ_SYNC_REQUEST_CONCURRENCY,
  LAMBDA_ROOT,
  LAYERS_ROOT,
  STACK_PREFIX,
} from '../constants';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';
import { SqsEventSource } from 'aws-cdk-lib/aws-lambda-event-sources';

/** Lambda stuff */
function buildLambda(scope: Construct, props: LambdaProps): LambdaObject {
  const lambdaNameToSnakeCase = camelCaseToSnakeCase(props.lambdaName);
  const lambdaRequirements = lambdaRequirementsMap[props.lambdaName];

  // Create the lambda function
  const lambdaFunction = new PythonUvFunction(scope, props.lambdaName, {
    entry: path.join(LAMBDA_ROOT, lambdaNameToSnakeCase + '_py'),
    runtime: lambda.Runtime.PYTHON_3_14,
    architecture: lambda.Architecture.ARM_64,
    index: lambdaNameToSnakeCase + '.py',
    handler: 'handler',
    timeout: props.lambdaName === 'handleMessages' ? Duration.seconds(300) : Duration.seconds(60),
    memorySize: 2048,
    includeOrcabusApiToolsLayer: lambdaRequirements.needsOrcabusApiToolsLayer,
    durableConfig: lambdaRequirements.needsDurableFunctionWrapper
      ? {
          executionTimeout: Duration.minutes(60),
          retentionPeriod: Duration.days(1),
        }
      : undefined,
  });

  // AwsSolutions-IAM4 - We need to add this for the lambda to work
  NagSuppressions.addResourceSuppressions(
    lambdaFunction,
    [
      {
        id: 'AwsSolutions-IAM4',
        reason: 'We use the default lambda execution role',
      },
    ],
    true
  );

  // Add in the fastq sync layer if required
  if (lambdaRequirements.needsFastqSyncLayer) {
    lambdaFunction.addLayers(props.fastqSyncLayer);
  }

  // If the lambda has an SQS event source, we need to add this in
  // Generate Event Request uses the launch ICA Source Event Queue
  if (props.lambdaName === 'handleMessages') {
    // Find the SQS queue from the props
    lambdaFunction.currentVersion.addEventSource(
      new SqsEventSource(props.sqsQueue, {
        maxConcurrency: DEFAULT_MAX_FASTQ_SYNC_REQUEST_CONCURRENCY,
        // Allow only one message per batch to be processed
        batchSize: 1,
      })
    );
  }

  // Add in sfn env vars
  if (props.lambdaName === 'handleMessages') {
    // Add the step function
    // Update the environment variable for the step function name
    // When we generate the state machine we will give the lambda permission to start the execution
    lambdaFunction.addEnvironment(
      'INITIALISE_TASK_TOKEN_FOR_FASTQ_ID_LIST_SFN_ARN',
      `arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:stateMachine:${STACK_PREFIX}--${props.initialiseTaskTokenForFastqIdListSfnName}`
    );
  }

  /* Return the function */
  return {
    lambdaName: props.lambdaName,
    lambdaFunction: lambdaFunction,
  };
}

export function buildAllLambdas(scope: Construct, props: BuildAllLambdaProps): LambdaObject[] {
  // Iterate over lambdaLayerToMapping and create the lambda functions
  const lambdaObjects: LambdaObject[] = [];
  for (const lambdaName of lambdaNameList) {
    lambdaObjects.push(
      buildLambda(scope, {
        ...props,
        lambdaName: lambdaName,
      })
    );
  }

  return lambdaObjects;
}

export function buildFastqSyncToolsLayer(scope: Construct): PythonLayerVersion {
  /**
     Build the fastq sync tools layer
     // Use getPythonUvDockerImage once we export this as a function from the
     // platform-cdk-constructs repo
     */
  return new PythonLayerVersion(scope, 'fastq-sync-tools-layer', {
    entry: path.join(LAYERS_ROOT, 'fastq_sync_tools_layer'),
    compatibleRuntimes: [lambda.Runtime.PYTHON_3_12],
    compatibleArchitectures: [lambda.Architecture.ARM_64],
    bundling: {
      image: getPythonUvDockerImage(),
      commandHooks: {
        // eslint-disable-next-line @typescript-eslint/no-unused-vars
        beforeBundling: function (inputDir: string, outputDir: string): string[] {
          return [];
        },
        afterBundling(inputDir: string, outputDir: string): string[] {
          return [
            `pip install ${inputDir} --target ${outputDir}`,
            `find ${outputDir} -name 'pandas' -exec rm -rf {}/tests/ \\;`,
          ];
        },
      },
    },
  });
}
