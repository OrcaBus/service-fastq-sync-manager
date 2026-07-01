import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { LayerVersion } from 'aws-cdk-lib/aws-lambda';
import { IQueue } from 'aws-cdk-lib/aws-sqs';
import { StepFunctionsName } from '../step-functions/interfaces';

export type LambdaName =
  // Shared function
  | 'checkFastqIdListAgainstRequirements'
  // Initialise task token
  | 'unlockCallbackId'
  // External Heartbeat monitor
  | 'checkRunningJobsForFastqIdList'
  // Launch Fastq List Row Requirements
  | 'getFastqAndRemainingRequirements'
  | 'launchRequirementJob'
  // Non sfn functions
  | 'handleMessages';

export const lambdaNameList: LambdaName[] = [
  // Shared function
  'checkFastqIdListAgainstRequirements',
  // Initialise task token
  'unlockCallbackId',
  // External Heartbeat monitor
  'checkRunningJobsForFastqIdList',
  // Launch Fastq List Row Requirements
  'getFastqAndRemainingRequirements',
  'launchRequirementJob',
  // Non sfn functions
  'handleMessages',
];

export interface LambdaRequirements {
  needsOrcabusApiToolsLayer?: boolean;
  needsFastqSyncLayer?: boolean;
  needsDurableFunctionWrapper?: boolean;
  needsCallbackPermissions?: boolean;
}

export const lambdaRequirementsMap: Record<LambdaName, LambdaRequirements> = {
  // Shared function
  checkFastqIdListAgainstRequirements: {
    needsOrcabusApiToolsLayer: true,
    needsFastqSyncLayer: true,
  },
  // Initialise task token
  unlockCallbackId: {
    needsCallbackPermissions: true,
  },
  // External Heartbeat monitor
  checkRunningJobsForFastqIdList: {
    needsOrcabusApiToolsLayer: true,
  },
  // Launch Fastq List Row Requirements
  getFastqAndRemainingRequirements: {
    needsOrcabusApiToolsLayer: true,
    needsFastqSyncLayer: true,
  },
  launchRequirementJob: {
    needsOrcabusApiToolsLayer: true,
    needsFastqSyncLayer: true,
  },
  // Non sfn functions
  handleMessages: {
    needsDurableFunctionWrapper: true,
  },
};

export interface BuildAllLambdaProps {
  fastqSyncLayer: LayerVersion;
  sqsQueue: IQueue;
  initialiseTaskTokenForFastqIdListSfnName: StepFunctionsName;
  pipelineCacheBucket: string;
  pipelineCachePrefix: string;
}

export interface LambdaProps extends BuildAllLambdaProps {
  lambdaName: LambdaName;
}

export interface LambdaObject {
  lambdaName: LambdaName;
  lambdaFunction: PythonFunction;
}
