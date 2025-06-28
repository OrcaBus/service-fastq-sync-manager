import { EventPattern } from 'aws-cdk-lib/aws-events';
import * as events from 'aws-cdk-lib/aws-events';
import {
  FASTQ_LIST_ROW_STATE_CHANGE_EVENT_DETAIL_TYPE,
  FASTQ_SYNC_EVENT_DETAIL_TYPE,
  FASTQ_SYNC_LEGACY_EVENT_DETAIL_TYPE,
} from '../constants';
import {
  FASTQ_MANAGER_EVENT_SOURCE,
  FASTQ_UNARCHIVING_JOB_EVENT_DETAIL_TYPE,
  FASTQ_UNARCHIVING_MANAGER_EVENT_SOURCE,
} from '../constants';
import { Construct } from 'constructs';
import { BuildEventProps, EventBridgeRuleObject, eventRuleNameList } from './interfaces';

/**
 * Legacy event
 */

function createNewFastqSetIdLegacyEventSyncEventPattern(): EventPattern {
  return {
    detailType: [FASTQ_SYNC_LEGACY_EVENT_DETAIL_TYPE],
    detail: {
      taskToken: [{ exists: true }],
      fastqSetId: [{ exists: true }],
    },
  };
}

/**
 * Listen to new fastq sync events
 */

function createNewFastqIdListEventSyncEventPattern(): EventPattern {
  return {
    detailType: [FASTQ_SYNC_EVENT_DETAIL_TYPE],
    detail: {
      taskToken: [{ exists: true }],
      payload: {
        fastqIdList: [{ exists: true }],
      },
    },
  };
}

function createNewFastqSetIdListEventSyncEventPattern(): EventPattern {
  return {
    detailType: [FASTQ_SYNC_EVENT_DETAIL_TYPE],
    detail: {
      taskToken: [{ exists: true }],
      payload: {
        fastqSetIdList: [{ exists: true }],
      },
    },
  };
}

/**
 * Listen to Fastq List Row state change events
 */
function createFastqListRowStateChangeEventPattern(): EventPattern {
  return {
    source: [FASTQ_MANAGER_EVENT_SOURCE],
    detailType: [FASTQ_LIST_ROW_STATE_CHANGE_EVENT_DETAIL_TYPE],
    detail: {
      status: [
        { 'equals-ignore-case': 'READ_SET_ADDED' },
        { 'equals-ignore-case': 'FILE_COMPRESSION_UPDATED' },
        { 'equals-ignore-case': 'QC_UPDATED' },
        { 'equals-ignore-case': 'NTSM_UPDATED' },
      ],
    },
  };
}

/**
 * Listen to Fastq Unarchiving Job state change events
 */
function createFastqUnarchivingJobStateChangeEventPattern(): EventPattern {
  return {
    source: [FASTQ_UNARCHIVING_MANAGER_EVENT_SOURCE],
    detailType: [FASTQ_UNARCHIVING_JOB_EVENT_DETAIL_TYPE],
    detail: {
      status: [{ 'equals-ignore-case': 'SUCCEEDED' }],
    },
  };
}

/**
 * Create event rules
 */

export function buildAllEventRules(
  scope: Construct,
  props: BuildEventProps
): EventBridgeRuleObject[] {
  const eventRulesList: EventBridgeRuleObject[] = [];
  for (const eventRule of eventRuleNameList) {
    switch (eventRule) {
      // Legacy fastq sync event
      case 'fastqSetSyncLegacyTaskTokenInitialisedRule': {
        eventRulesList.push({
          ruleName: eventRule,
          ruleObject: new events.Rule(scope, eventRule, {
            ruleName: eventRule,
            eventBus: props.eventBus,
            eventPattern: createNewFastqSetIdLegacyEventSyncEventPattern(),
          }),
        });
        break;
      }

      // Task token initialised for new fastq sync event
      case 'fastqSyncTaskTokenInitialisedRule': {
        eventRulesList.push({
          ruleName: eventRule,
          ruleObject: new events.Rule(scope, eventRule, {
            ruleName: eventRule,
            eventBus: props.eventBus,
            eventPattern: createNewFastqIdListEventSyncEventPattern(),
          }),
        });
        break;
      }
      case 'fastqSetSyncTaskTokenInitialisedRule': {
        eventRulesList.push({
          ruleName: eventRule,
          ruleObject: new events.Rule(scope, eventRule, {
            ruleName: eventRule,
            eventBus: props.eventBus,
            eventPattern: createNewFastqSetIdListEventSyncEventPattern(),
          }),
        });
        break;
      }

      // Fastq List Row state change event
      case 'fastqListRowStateChange': {
        eventRulesList.push({
          ruleName: eventRule,
          ruleObject: new events.Rule(scope, eventRule, {
            ruleName: eventRule,
            eventBus: props.eventBus,
            eventPattern: createFastqListRowStateChangeEventPattern(),
          }),
        });
        break;
      }

      // Fastq Unarchiving Job state change event
      case 'fastqUnarchivingStateChange': {
        eventRulesList.push({
          ruleName: eventRule,
          ruleObject: new events.Rule(scope, eventRule, {
            ruleName: eventRule,
            eventBus: props.eventBus,
            eventPattern: createFastqUnarchivingJobStateChangeEventPattern(),
          }),
        });
        break;
      }
    }
  }

  return eventRulesList;
}
