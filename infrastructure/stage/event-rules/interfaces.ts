/*
List of interfaces used for event rules
 */

import { IEventBus, Rule } from 'aws-cdk-lib/aws-events';

export type EventRuleName =
  // Legacy rule
  | 'fastqSetSyncLegacyTaskTokenInitialisedRule'
  // Task Token Initialised rules
  | 'fastqSyncTaskTokenInitialisedRule'
  | 'fastqSetSyncTaskTokenInitialisedRule'
  // Fastq List row updated
  | 'fastqStateChange'
  // Fastq Unarchiving updated
  | 'fastqUnarchivingStateChange';

export const eventRuleNameList: EventRuleName[] = [
  // Legacy rule
  'fastqSetSyncLegacyTaskTokenInitialisedRule',
  // Task Token Initialised rules
  'fastqSyncTaskTokenInitialisedRule',
  'fastqSetSyncTaskTokenInitialisedRule',
  // Fastq List row updated
  'fastqStateChange',
  // Fastq Unarchiving updated
  'fastqUnarchivingStateChange',
];

export interface BuildEventProps {
  eventBus: IEventBus;
}

export interface EventBridgeRuleObject {
  ruleName: EventRuleName;
  ruleObject: Rule;
}
