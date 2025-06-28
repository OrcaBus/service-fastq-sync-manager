import { Construct } from 'constructs';
import { TableV2 } from 'aws-cdk-lib/aws-dynamodb';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import {
  DEFAULT_PARTITION_KEY_NAME,
  DEFAULT_SORT_KEY_NAME,
} from '@orcabus/platform-cdk-constructs/dynamodb/config';
import { RemovalPolicy } from 'aws-cdk-lib';
import { TaskTokenTableProps } from './interfaces';

export function buildTaskTokenTable(scope: Construct, props: TaskTokenTableProps): TableV2 {
  return new dynamodb.TableV2(scope, props.tableName, {
    /* Set the table name */
    tableName: props.tableName,
    /* Unique id across the sort key */
    partitionKey: {
      name: DEFAULT_PARTITION_KEY_NAME,
      type: dynamodb.AttributeType.STRING,
    },
    /* Categorical key */
    sortKey: {
      name: DEFAULT_SORT_KEY_NAME,
      type: dynamodb.AttributeType.STRING,
    },
    /* Backup / removal policies */
    // This table is used for task tokens, which are ephemeral and should not persist beyond their lifecycle.
    // So we set the removal policy to DESTROY.
    removalPolicy: RemovalPolicy.DESTROY,
    pointInTimeRecoverySpecification: {
      pointInTimeRecoveryEnabled: true,
    },
  });
}
