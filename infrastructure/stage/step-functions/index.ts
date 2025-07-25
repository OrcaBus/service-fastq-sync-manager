/*
Build the step functions
 */

// Imports
import * as sfn from 'aws-cdk-lib/aws-stepfunctions';
import { Construct } from 'constructs';
import * as path from 'path';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as cdk from 'aws-cdk-lib';

// Local interfaces
import {
  initialiseTaskTokenForFastqIdListSfnName,
  launchFastqListRowRequirementsSfnName,
  SfnObject,
  SfnProps,
  SfnPropsWithObject,
  SfnsProps,
  stepFunctionLambdaMap,
  stepFunctionsNames,
  stepFunctionsRequirementsMap,
} from './interfaces';
import { camelCaseToSnakeCase } from '../utils';
import { NagSuppressions } from 'cdk-nag';
import { SFN_PREFIX, STEP_FUNCTIONS_ROOT } from '../constants';
import { StateMachine } from 'aws-cdk-lib/aws-stepfunctions';

/** Step Function stuff */
function createStateMachineDefinitionSubstitutions(props: SfnProps): {
  [key: string]: string;
} {
  const definitionSubstitutions: { [key: string]: string } = {};

  const sfnRequirements = stepFunctionsRequirementsMap[props.stateMachineName];
  const lambdaFunctionNamesInSfn = stepFunctionLambdaMap[props.stateMachineName];
  const lambdaFunctions = props.lambdaObjects.filter((lambdaObject) =>
    lambdaFunctionNamesInSfn.includes(lambdaObject.lambdaName)
  );

  /* Substitute lambdas in the state machine definition */
  for (const lambdaObject of lambdaFunctions) {
    const sfnSubstitutionKey = `__${camelCaseToSnakeCase(lambdaObject.lambdaName)}_lambda_function_arn__`;
    definitionSubstitutions[sfnSubstitutionKey] =
      lambdaObject.lambdaFunction.currentVersion.functionArn;
  }

  /* Sfn Requirements */
  if (sfnRequirements.needsDbAccess) {
    definitionSubstitutions['__dynamodb_table_name__'] = props.tableObj.tableName;
  }

  if (sfnRequirements.needsSfnExecutionAccess) {
    definitionSubstitutions['__launch_requirements_sfn_arn__'] =
      `arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:stateMachine:${SFN_PREFIX}-${launchFastqListRowRequirementsSfnName}`;
    definitionSubstitutions['__initialise_task_token_for_fastq_id_list_sfn_arn__'] =
      `arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:stateMachine:${SFN_PREFIX}-${initialiseTaskTokenForFastqIdListSfnName}`;
  }

  return definitionSubstitutions;
}

function wireUpStateMachinePermissions(props: SfnPropsWithObject): void {
  /* Wire up lambda permissions */
  const sfnRequirements = stepFunctionsRequirementsMap[props.stateMachineName];

  const lambdaFunctionNamesInSfn = stepFunctionLambdaMap[props.stateMachineName];
  const lambdaFunctions = props.lambdaObjects.filter((lambdaObject) =>
    lambdaFunctionNamesInSfn.includes(lambdaObject.lambdaName)
  );

  /* Allow the state machine to invoke the lambda function */
  for (const lambdaObject of lambdaFunctions) {
    lambdaObject.lambdaFunction.currentVersion.grantInvoke(props.stateMachineObject);
  }

  /* Permissions */
  /* Grant the state machine permissions to read from the DynamoDB table */
  if (sfnRequirements.needsDbAccess) {
    props.tableObj.grantReadWriteData(props.stateMachineObject);
  }

  if (sfnRequirements.needsSendTaskExecutionAccess) {
    props.stateMachineObject.addToRolePolicy(
      new iam.PolicyStatement({
        resources: [`arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:stateMachine:*`],
        actions: ['states:SendTaskSuccess', 'states:SendTaskFailure', 'states:SendTaskHeartbeat'],
      })
    );

    // Will need cdk nag suppressions for this
    // Because we are using a wildcard for an IAM Resource policy
    NagSuppressions.addResourceSuppressions(
      props.stateMachineObject,
      [
        {
          id: 'AwsSolutions-IAM5',
          reason: 'Need ability to send task success/failure/heartbeat to any state machine',
        },
      ],
      true
    );
  }
}

function buildStepFunction(scope: Construct, props: SfnProps): SfnObject {
  const sfnNameToSnakeCase = camelCaseToSnakeCase(props.stateMachineName);

  /* Create the state machine definition substitutions */
  const stateMachine = new sfn.StateMachine(scope, props.stateMachineName, {
    stateMachineName: `${SFN_PREFIX}-${props.stateMachineName}`,
    definitionBody: sfn.DefinitionBody.fromFile(
      path.join(STEP_FUNCTIONS_ROOT, sfnNameToSnakeCase + `_sfn_template.asl.json`)
    ),
    definitionSubstitutions: createStateMachineDefinitionSubstitutions(props),
  });

  /* Grant the state machine permissions */
  wireUpStateMachinePermissions({
    stateMachineObject: stateMachine,
    ...props,
  });

  /* Nag Suppressions */
  /* AwsSolutions-SF1 - We don't need ALL events to be logged */
  /* AwsSolutions-SF2 - We also don't need X-Ray tracing */
  NagSuppressions.addResourceSuppressions(
    stateMachine,
    [
      {
        id: 'AwsSolutions-SF1',
        reason: 'We do not need all events to be logged',
      },
      {
        id: 'AwsSolutions-SF2',
        reason: 'We do not need X-Ray tracing',
      },
    ],
    true
  );

  /* Return as a state machine object property */
  return {
    ...props,
    stateMachineObject: stateMachine,
  };
}

export function buildAllStepFunctions(scope: Construct, props: SfnsProps): SfnObject[] {
  // Initialize the step function objects
  const sfnObjects = [] as SfnObject[];

  // Iterate over lambdaLayerToMapping and create the lambda functions
  for (const sfnName of stepFunctionsNames) {
    sfnObjects.push(
      buildStepFunction(scope, {
        stateMachineName: sfnName,
        ...props,
      })
    );
  }

  // Some unique cases we need to handle AFTER the main loop
  for (const sfnName of stepFunctionsNames) {
    /* Wire up lambda permissions */
    const sfnRequirements = stepFunctionsRequirementsMap[sfnName];
    const sfnObject = <StateMachine>(
      sfnObjects.find((sfnObject) => sfnObject.stateMachineName === sfnName)?.stateMachineObject
    );

    /* Sfn Requirements */
    if (sfnRequirements.needsSfnExecutionAccess) {
      // Grant start execution permissions
      // We use the step function name, rather than the object to prevent circular dependencies
      sfnObject.addToRolePolicy(
        new iam.PolicyStatement({
          resources: [
            `arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:stateMachine:${SFN_PREFIX}-${launchFastqListRowRequirementsSfnName}`,
            `arn:aws:states:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:stateMachine:${SFN_PREFIX}-${initialiseTaskTokenForFastqIdListSfnName}`,
          ],
          actions: ['states:StartExecution'],
        })
      );

      // Because we run a nested state machine, we need to add the permissions to the state machine role
      // See https://stackoverflow.com/questions/60612853/nested-step-function-in-a-step-function-unknown-error-not-authorized-to-cr
      sfnObject.addToRolePolicy(
        new iam.PolicyStatement({
          resources: [
            `arn:aws:events:${cdk.Aws.REGION}:${cdk.Aws.ACCOUNT_ID}:rule/StepFunctionsGetEventsForStepFunctionsExecutionRule`,
          ],
          actions: ['events:PutTargets', 'events:PutRule', 'events:DescribeRule'],
        })
      );

      // Because this will include 'describeExecution' we need to suppress the cdk nag
      NagSuppressions.addResourceSuppressions(
        sfnObject,
        [
          {
            id: 'AwsSolutions-IAM5',
            reason: 'Need ability to execute the sfn steps copy state machine',
          },
        ],
        true
      );
    }
  }

  return sfnObjects;
}
