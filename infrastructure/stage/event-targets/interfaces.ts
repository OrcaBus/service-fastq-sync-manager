/*
Event target interfaces
 */

import { Rule } from 'aws-cdk-lib/aws-events';
import { StateMachine } from 'aws-cdk-lib/aws-stepfunctions';
import { EventBridgeRuleObject } from '../event-rules/interfaces';
import { SfnObject } from '../step-functions/interfaces';

export type EventTargets =
  // Legacy
  | 'fastqSetSyncLegacyTaskTokenToFastqSetInitialiserSfn'
  // Task token requests to sfns
  | 'fastqSyncTaskTokenToFastqSetInitialiserSfn'
  | 'fastqSetSyncTaskTokenToFastqIdInitialiserSfn'
  // Fastq ID Updated
  | 'fastqListRowStateChangeToFastqIdUpdatedSfn'
  // Fastq Unarchiving updated
  | 'fastqUnarchivingJobStateChangeToFastqIdUpdatedSfn'
  // Scheduler
  | 'heartBeatMonitorSchedulerToExternalHeartBeatMonitorSfn';

export const eventTargetsList: EventTargets[] = [
  // Legacy
  'fastqSetSyncLegacyTaskTokenToFastqSetInitialiserSfn',
  // Task token requests to sfns
  'fastqSyncTaskTokenToFastqSetInitialiserSfn',
  'fastqSetSyncTaskTokenToFastqIdInitialiserSfn',
  // Fastq ID Updated
  'fastqListRowStateChangeToFastqIdUpdatedSfn',
  // Fastq Unarchiving updated
  'fastqUnarchivingJobStateChangeToFastqIdUpdatedSfn',
];

export interface AddSfnAsEventBridgeTargetProps {
  stateMachineObj: StateMachine;
  eventBridgeRuleObj: Rule;
}

export interface EventBridgeTargetsProps {
  eventBridgeRuleObjects: EventBridgeRuleObject[];
  stepFunctionObjects: SfnObject[];
}
