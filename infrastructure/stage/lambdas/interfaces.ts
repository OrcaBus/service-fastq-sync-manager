import { PythonFunction } from '@aws-cdk/aws-lambda-python-alpha';
import { LayerVersion } from 'aws-cdk-lib/aws-lambda';

export type LambdaNameList =
  | 'checkFastqIdListAgainstRequirements'
  | 'checkRunningJobsForFastqIdList'
  | 'getFastqAndRemainingRequirements'
  | 'getFastqIdListFromFastqSetIdList'
  | 'launchRequirementJob';

export const lambdaNameList: LambdaNameList[] = [
  'checkFastqIdListAgainstRequirements',
  'checkRunningJobsForFastqIdList',
  'getFastqAndRemainingRequirements',
  'getFastqIdListFromFastqSetIdList',
  'launchRequirementJob',
];

export interface LambdaRequirements {
  needsOrcabusApiToolsLayer?: boolean;
  needsFastqSyncLayer?: boolean;
}

export const lambdaRequirementsMap: Record<LambdaNameList, LambdaRequirements> = {
  checkFastqIdListAgainstRequirements: {
    needsOrcabusApiToolsLayer: true,
    needsFastqSyncLayer: true,
  },
  checkRunningJobsForFastqIdList: {
    needsOrcabusApiToolsLayer: true,
  },
  getFastqAndRemainingRequirements: {
    needsOrcabusApiToolsLayer: true,
    needsFastqSyncLayer: true,
  },
  getFastqIdListFromFastqSetIdList: {
    needsOrcabusApiToolsLayer: true,
  },
  launchRequirementJob: {
    needsOrcabusApiToolsLayer: true,
    needsFastqSyncLayer: true,
  },
};

export interface LambdaProps {
  lambdaName: LambdaNameList;
  fastqSyncLayer: LayerVersion;
}

export type BuildAllLambdaProps = Omit<LambdaProps, 'lambdaName'>;

export interface LambdaObject extends Omit<LambdaProps, 'fastqSyncLayer'> {
  lambdaFunction: PythonFunction;
}
