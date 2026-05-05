import { StateMachine } from 'aws-cdk-lib/aws-stepfunctions';
import { LambdaName, LambdaObject } from '../lambdas/interfaces';
import { IEventBus } from 'aws-cdk-lib/aws-events';
import { ITableV2 } from 'aws-cdk-lib/aws-dynamodb';
import { IQueue } from 'aws-cdk-lib/aws-sqs';

export type StepFunctionsName =
  // Initialisation
  | 'sendFastqSyncRequestToQueue'
  | 'initialiseTaskTokenForFastqIdList'
  // Launch jobs as required
  | 'launchFastqListRowRequirements'
  // Listen to fastq related events to release task tokens
  | 'fastqIdUpdated'
  // External heartbeat monitoring
  | 'externalHeartbeatMonitor';

export const stepFunctionsNames: StepFunctionsName[] = [
  // Initialisation
  'sendFastqSyncRequestToQueue',
  'initialiseTaskTokenForFastqIdList',
  // Launch jobs as required
  'launchFastqListRowRequirements',
  // Listen to fastq related events to release task tokens
  'fastqIdUpdated',
  // External heartbeat monitoring
  'externalHeartbeatMonitor',
];

export const launchFastqListRowRequirementsSfnName: StepFunctionsName =
  'launchFastqListRowRequirements';
export const initialiseTaskTokenForFastqIdListSfnName: StepFunctionsName =
  'initialiseTaskTokenForFastqIdList';

export interface StepFunctionsRequirements {
  needsDbAccess?: boolean;
  needsSfnExecutionAccess?: boolean;
  needsSendTaskExecutionAccess?: boolean;
  needsHeartBeatRuleSwitchAccess?: boolean;
  needsDistributedMapPermissions?: boolean;
  needsSqsSendMessagePermissions?: boolean;
}

export const stepFunctionsRequirementsMap: Record<StepFunctionsName, StepFunctionsRequirements> = {
  // Initialisation
  sendFastqSyncRequestToQueue: {
    needsSqsSendMessagePermissions: true,
  },
  initialiseTaskTokenForFastqIdList: {
    needsDbAccess: true,
    needsSfnExecutionAccess: true,
    needsSendTaskExecutionAccess: true,
    needsHeartBeatRuleSwitchAccess: true,
  },
  // Launch jobs as required
  launchFastqListRowRequirements: {},
  // Listen to fastq related events to release task tokens
  fastqIdUpdated: {
    needsDbAccess: true,
    needsSfnExecutionAccess: true,
    needsSendTaskExecutionAccess: true,
  },
  // External heartbeat monitoring
  externalHeartbeatMonitor: {
    needsDbAccess: true,
    needsSendTaskExecutionAccess: true,
    needsHeartBeatRuleSwitchAccess: true,
    needsDistributedMapPermissions: true,
  },
};

// Map the lambda functions to their step function names
export const stepFunctionLambdaMap: Record<StepFunctionsName, LambdaName[]> = {
  sendFastqSyncRequestToQueue: [],
  initialiseTaskTokenForFastqIdList: ['checkFastqIdListAgainstRequirements', 'unlockCallbackId'],
  launchFastqListRowRequirements: ['getFastqAndRemainingRequirements', 'launchRequirementJob'],
  fastqIdUpdated: ['checkFastqIdListAgainstRequirements'],
  externalHeartbeatMonitor: [
    'checkRunningJobsForFastqIdList',
    'checkFastqIdListAgainstRequirements',
  ],
};

export interface SfnsProps {
  // List of lambda functions that are used in the state machine
  lambdaObjects: LambdaObject[];
  // Event Objects
  eventBus: IEventBus;
  // Table objects
  tableObj: ITableV2;
  // Queue
  sqsQueue: IQueue;
}

export interface SfnProps extends SfnsProps {
  // Name of the state machine
  stateMachineName: StepFunctionsName;
}

export interface SfnPropsWithObject extends SfnProps {
  stateMachineObj: StateMachine;
}

export interface SfnObject {
  stateMachineName: StepFunctionsName;
  stateMachineObj: StateMachine;
}
