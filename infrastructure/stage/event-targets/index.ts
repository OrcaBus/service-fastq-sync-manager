/**
 * Map the event rules to the step functions that they trigger
 */
import {
  AddSfnAsEventBridgeTargetProps,
  EventBridgeTargetsProps,
  eventTargetsList,
} from './interfaces';
import * as eventsTargets from 'aws-cdk-lib/aws-events-targets';
import * as events from 'aws-cdk-lib/aws-events';
import { EventField } from 'aws-cdk-lib/aws-events';

function buildSfnEventBridgeTarget(props: AddSfnAsEventBridgeTargetProps): void {
  props.eventBridgeRuleObj.addTarget(
    new eventsTargets.SfnStateMachine(props.stateMachineObj, {
      input: events.RuleTargetInput.fromEventPath('$.detail'),
    })
  );
}

function buildLegacySfnEventBridgeTarget(props: AddSfnAsEventBridgeTargetProps): void {
  props.eventBridgeRuleObj.addTarget(
    new eventsTargets.SfnStateMachine(props.stateMachineObj, {
      input: events.RuleTargetInput.fromObject({
        taskToken: EventField.fromPath('$.detail.taskToken'),
        payload: {
          fastqSetIdList: [EventField.fromPath('$.detail.fastqSetId')],
          requirements: EventField.fromPath('$.detail.requirements'),
          forceUnarchiving: EventField.fromPath('$.detail.forceUnarchiving'),
        },
      }),
    })
  );
}

function buildFastqIdUpdatedTarget(props: AddSfnAsEventBridgeTargetProps): void {
  props.eventBridgeRuleObj.addTarget(
    new eventsTargets.SfnStateMachine(props.stateMachineObj, {
      input: events.RuleTargetInput.fromObject({
        fastqId: EventField.fromPath('$.detail.id'),
      }),
    })
  );
}

export function buildAllEventBridgeTargets(props: EventBridgeTargetsProps) {
  /* Iterate over each event bridge rule and add the target */
  for (const eventBridgeTargetsName of eventTargetsList) {
    // // Fastq ID Updated
    // 'fastqListRowStateChangeToFastqIdUpdatedSfn',
    // // Fastq Unarchiving updated
    // 'fastqUnarchivingJobStateChangeToFastqIdUpdatedSfn',

    switch (eventBridgeTargetsName) {
      // Legacy
      case 'fastqSetSyncLegacyTaskTokenToFastqSetInitialiserSfn': {
        buildLegacySfnEventBridgeTarget(<AddSfnAsEventBridgeTargetProps>{
          eventBridgeRuleObj: props.eventBridgeRuleObjects.find(
            (eventBridgeObject) =>
              eventBridgeObject.ruleName === 'fastqSetSyncLegacyTaskTokenInitialisedRule'
          )?.ruleObject,
          stateMachineObj: props.stepFunctionObjects.find(
            (eventBridgeObject) =>
              eventBridgeObject.stateMachineName === 'initialiseTaskTokenForFastqSetIdList'
          )?.stateMachineObject,
        });
        break;
      }
      // Task token requests to sfns
      case 'fastqSyncTaskTokenToFastqSetInitialiserSfn': {
        buildSfnEventBridgeTarget(<AddSfnAsEventBridgeTargetProps>{
          eventBridgeRuleObj: props.eventBridgeRuleObjects.find(
            (eventBridgeObject) =>
              eventBridgeObject.ruleName === 'fastqSyncTaskTokenInitialisedRule'
          )?.ruleObject,
          stateMachineObj: props.stepFunctionObjects.find(
            (eventBridgeObject) =>
              eventBridgeObject.stateMachineName === 'initialiseTaskTokenForFastqIdList'
          )?.stateMachineObject,
        });
        break;
      }
      case 'fastqSetSyncTaskTokenToFastqIdInitialiserSfn': {
        buildSfnEventBridgeTarget(<AddSfnAsEventBridgeTargetProps>{
          eventBridgeRuleObj: props.eventBridgeRuleObjects.find(
            (eventBridgeObject) =>
              eventBridgeObject.ruleName === 'fastqSetSyncTaskTokenInitialisedRule'
          )?.ruleObject,
          stateMachineObj: props.stepFunctionObjects.find(
            (eventBridgeObject) =>
              eventBridgeObject.stateMachineName === 'initialiseTaskTokenForFastqSetIdList'
          )?.stateMachineObject,
        });
        break;
      }
      // fastqListRowStateChangeToFastqIdUpdatedSfn
      case 'fastqListRowStateChangeToFastqIdUpdatedSfn': {
        buildFastqIdUpdatedTarget(<AddSfnAsEventBridgeTargetProps>{
          eventBridgeRuleObj: props.eventBridgeRuleObjects.find(
            (eventBridgeObject) => eventBridgeObject.ruleName === 'fastqStateChange'
          )?.ruleObject,
          stateMachineObj: props.stepFunctionObjects.find(
            (eventBridgeObject) => eventBridgeObject.stateMachineName === 'fastqIdUpdated'
          )?.stateMachineObject,
        });
        break;
      }
      // fastqUnarchivingJobStateChangeToFastqIdUpdatedSfn
      case 'fastqUnarchivingJobStateChangeToFastqIdUpdatedSfn': {
        buildSfnEventBridgeTarget(<AddSfnAsEventBridgeTargetProps>{
          eventBridgeRuleObj: props.eventBridgeRuleObjects.find(
            (eventBridgeObject) => eventBridgeObject.ruleName === 'fastqUnarchivingStateChange'
          )?.ruleObject,
          stateMachineObj: props.stepFunctionObjects.find(
            (eventBridgeObject) => eventBridgeObject.stateMachineName === 'fastqIdUpdated'
          )?.stateMachineObject,
        });
        break;
      }
    }
  }
}
