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
import { camelCaseToSnakeCase } from '../utils';
import { getPythonUvDockerImage, PythonUvFunction } from '@orcabus/platform-cdk-constructs/lambda';
import * as path from 'path';
import { LAMBDA_ROOT, LAYERS_ROOT } from '../constants';
import { PythonLayerVersion } from '@aws-cdk/aws-lambda-python-alpha';

/** Lambda stuff */
function buildLambda(scope: Construct, props: LambdaProps): LambdaObject {
  const lambdaNameToSnakeCase = camelCaseToSnakeCase(props.lambdaName);
  const lambdaRequirements = lambdaRequirementsMap[props.lambdaName];

  // Create the lambda function
  const lambdaFunction = new PythonUvFunction(scope, props.lambdaName, {
    entry: path.join(LAMBDA_ROOT, lambdaNameToSnakeCase + '_py'),
    runtime: lambda.Runtime.PYTHON_3_12,
    architecture: lambda.Architecture.ARM_64,
    index: lambdaNameToSnakeCase + '.py',
    handler: 'handler',
    timeout: Duration.seconds(60),
    memorySize: 2048,
    includeOrcabusApiToolsLayer: lambdaRequirements.needsOrcabusApiToolsLayer,
  });

  // Add in the fastq sync layer if required
  if (lambdaRequirements.needsFastqSyncLayer) {
    lambdaFunction.addLayers(props.fastqSyncLayer);
    lambdaFunction.addEnvironment(
      'BYOB_BUCKET_PREFIX',
      `s3://${props.pipelineCacheBucketName}/${props.pipelineCacheKeyPrefix}`
    );
  }

  // AwsSolutions-L1 - We'll migrate to PYTHON_3_13 ASAP, soz
  // AwsSolutions-IAM4 - We need to add this for the lambda to work
  NagSuppressions.addResourceSuppressions(
    lambdaFunction,
    [
      {
        id: 'AwsSolutions-L1',
        reason: 'Will migrate to PYTHON_3_13 ASAP, soz',
      },
    ],
    true
  );

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
