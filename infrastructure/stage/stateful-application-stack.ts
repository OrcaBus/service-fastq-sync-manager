import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { buildTaskTokenTable } from './dynamodb';
import { StatefulApplicationConfig } from './interfaces';

export type StatefulApplicationStackProps = cdk.StackProps & StatefulApplicationConfig;

export class StatefulApplicationStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: StatefulApplicationStackProps) {
    super(scope, id, props);

    /**
     * Define your stack to be deployed in stages here
     *
     */

    // Build the dynamodb tables
    buildTaskTokenTable(this, {
      tableName: props.tableName,
    });
  }
}
