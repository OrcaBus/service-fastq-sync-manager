/*
List of interfaces used for event rules
 */

import { IEventBus, Rule } from 'aws-cdk-lib/aws-events';
import { Duration } from 'aws-cdk-lib';
import { HEART_BEAT_SCHEDULER_RULE_NAME } from '../constants';

export type EventRuleName =
  // Task Token Initialised rules
  | 'fastqSyncTaskTokenInitialisedRule'
  // Fastq List row updated
  | 'fastqStateChange'
  // Fastq Unarchiving updated
  | 'fastqUnarchivingStateChange'
  // Internal Heartbeat
  | typeof HEART_BEAT_SCHEDULER_RULE_NAME;

export const eventRuleNameList: EventRuleName[] = [
  // Task Token Initialised rules
  'fastqSyncTaskTokenInitialisedRule',
  // Fastq List row updated
  'fastqStateChange',
  // Fastq Unarchiving updated
  'fastqUnarchivingStateChange',
  // Internal Heartbeat
  HEART_BEAT_SCHEDULER_RULE_NAME,
];

export interface EventBridgeRuleProps {
  ruleName: EventRuleName;
  eventBus: IEventBus;
}

export type EventBridgeRulesProps = Omit<EventBridgeRuleProps, 'ruleName'>;

export interface HeartBeatEventBridgeRuleProps extends Omit<EventBridgeRuleProps, 'eventBus'> {
  scheduleDuration?: Duration;
}

export interface EventBridgeRuleObject {
  ruleName: EventRuleName;
  ruleObject: Rule;
}
