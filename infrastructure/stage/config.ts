import { StatefulApplicationConfig, StatelessApplicationConfig } from './interfaces';
import { FASTQ_SYNC_TASK_TOKEN_TABLE_NAME } from './constants';
import { EVENT_BUS_NAME } from '@orcabus/platform-cdk-constructs/shared-config/event-bridge';

export const getStatefulApplicationProps = (): StatefulApplicationConfig => {
  return {
    tableName: FASTQ_SYNC_TASK_TOKEN_TABLE_NAME,
  };
};

export const getStatelessApplicationProps = (): StatelessApplicationConfig => {
  return {
    eventBusName: EVENT_BUS_NAME,
    tableName: FASTQ_SYNC_TASK_TOKEN_TABLE_NAME,
  };
};
