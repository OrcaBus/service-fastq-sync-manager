/*
Event target interfaces
 */

import { Rule } from 'aws-cdk-lib/aws-events';
import { StateMachine } from 'aws-cdk-lib/aws-stepfunctions';
import { EventBridgeRuleObject } from '../event-rules/interfaces';
import { SfnObject } from '../step-functions/interfaces';

export type EventTargets =
  // Task token requests to sfns
  | 'fastqSyncTaskTokenToFastqSetInitialiserSfn'
  // Fastq ID Updated
  | 'fastqListRowStateChangeToFastqIdUpdatedSfn'
  // Fastq Unarchiving updated
  | 'fastqUnarchivingJobStateChangeToFastqIdUpdatedSfn'
  // Scheduler
  | 'heartBeatMonitorSchedulerToExternalHeartBeatMonitorSfn'
  // Fastq Set state change to Fastq Set ID Updated SFN
  | 'fastqSetStateChangeToFastqSetIdUpdatedSfn'
  // Fastq Set sync task token to Fastq Set Initialiser SFN
  | 'fastqSetSyncTaskTokenToFastqSetInitialiserSfn';

export const eventTargetsList: EventTargets[] = [
  // Task token requests to sfns
  'fastqSyncTaskTokenToFastqSetInitialiserSfn',
  // Fastq ID Updated
  'fastqListRowStateChangeToFastqIdUpdatedSfn',
  // Fastq Unarchiving updated
  'fastqUnarchivingJobStateChangeToFastqIdUpdatedSfn',
  // Scheduler
  'heartBeatMonitorSchedulerToExternalHeartBeatMonitorSfn',
  // Fastq Set state change to Fastq Set ID Updated SFN
  'fastqSetStateChangeToFastqSetIdUpdatedSfn',
  // Fastq Set sync task token to Fastq Set Initialiser SFN
  'fastqSetSyncTaskTokenToFastqSetInitialiserSfn',
];

export interface AddSfnAsEventBridgeTargetProps {
  stateMachineObj: StateMachine;
  eventBridgeRuleObj: Rule;
}

export interface EventBridgeTargetsProps {
  eventBridgeRuleObjects: EventBridgeRuleObject[];
  stepFunctionObjects: SfnObject[];
}
