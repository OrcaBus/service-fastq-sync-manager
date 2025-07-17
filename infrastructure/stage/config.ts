import { StatefulApplicationConfig, StatelessApplicationConfig } from './interfaces';
import { FASTQ_SYNC_TASK_TOKEN_TABLE_NAME } from './constants';
import { EVENT_BUS_NAME } from '@orcabus/platform-cdk-constructs/shared-config/event-bridge';
import {
  PIPELINE_CACHE_BUCKET,
  PIPELINE_CACHE_PREFIX,
} from '@orcabus/platform-cdk-constructs/shared-config/s3';
import { StageName } from '@orcabus/platform-cdk-constructs/shared-config/accounts';

export const getStatefulApplicationProps = (): StatefulApplicationConfig => {
  return {
    tableName: FASTQ_SYNC_TASK_TOKEN_TABLE_NAME,
  };
};

export const getStatelessApplicationProps = (stage: StageName): StatelessApplicationConfig => {
  return {
    eventBusName: EVENT_BUS_NAME,
    tableName: FASTQ_SYNC_TASK_TOKEN_TABLE_NAME,
    pipelineCacheBucketName: PIPELINE_CACHE_BUCKET[stage],
    pipelineCacheKeyPrefix: PIPELINE_CACHE_PREFIX[stage],
  };
};
