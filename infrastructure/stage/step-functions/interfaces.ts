import { StateMachine } from 'aws-cdk-lib/aws-stepfunctions';
import { LambdaNameList, LambdaObject } from '../lambdas/interfaces';
import { IEventBus } from 'aws-cdk-lib/aws-events';
import { ITableV2 } from 'aws-cdk-lib/aws-dynamodb';

export type StepFunctionsName =
  // Initialisation
  | 'initialiseTaskTokenForFastqIdList'
  | 'initialiseTaskTokenForFastqSetIdList'
  // Launch jobs as required
  | 'launchFastqListRowRequirements'
  // Listen to fastq related events to release task tokens
  | 'fastqIdUpdated'
  // External heartbeat monitoring
  | 'externalHeartbeatMonitor';

export const stepFunctionsNames: StepFunctionsName[] = [
  // Initialisation
  'initialiseTaskTokenForFastqIdList',
  'initialiseTaskTokenForFastqSetIdList',
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
}

export const stepFunctionsRequirementsMap: Record<StepFunctionsName, StepFunctionsRequirements> = {
  // Initialisation
  initialiseTaskTokenForFastqIdList: {
    needsDbAccess: true,
    needsSfnExecutionAccess: true,
    needsSendTaskExecutionAccess: true,
    needsHeartBeatRuleSwitchAccess: true,
  },
  initialiseTaskTokenForFastqSetIdList: {
    needsSfnExecutionAccess: true,
    needsSendTaskExecutionAccess: true,
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
  },
};

// Map the lambda functions to their step function names
export const stepFunctionLambdaMap: Record<StepFunctionsName, LambdaNameList[]> = {
  initialiseTaskTokenForFastqIdList: ['checkFastqIdListAgainstRequirements'],
  initialiseTaskTokenForFastqSetIdList: ['getFastqIdListFromFastqSetIdList'],
  launchFastqListRowRequirements: ['getFastqAndRemainingRequirements', 'launchRequirementJob'],
  fastqIdUpdated: ['checkFastqIdListAgainstRequirements'],
  externalHeartbeatMonitor: ['checkRunningJobsForFastqIdList'],
};

export interface SfnProps {
  // Name of the state machine
  stateMachineName: StepFunctionsName;
  // List of lambda functions that are used in the state machine
  lambdaObjects: LambdaObject[];
  // Event Objects
  eventBus: IEventBus;
  // Table objects
  tableObj: ITableV2;
}

export interface SfnPropsWithObject extends SfnProps {
  stateMachineObj: StateMachine;
}

export type SfnsProps = Omit<SfnProps, 'stateMachineName'>;

export interface SfnObject {
  stateMachineName: StepFunctionsName;
  stateMachineObj: StateMachine;
}
