import { App, Aspects, Stack } from 'aws-cdk-lib';
import { Annotations, Match } from 'aws-cdk-lib/assertions';
import { SynthesisMessage } from 'aws-cdk-lib/cx-api';
import { AwsSolutionsChecks, NagSuppressions } from 'cdk-nag';
import { StatelessApplicationStack } from '../infrastructure/stage/stateless-application-stack';
import {
  getStatefulApplicationProps,
  getStatelessApplicationProps,
} from '../infrastructure/stage/config';
import { StatefulApplicationStack } from '../infrastructure/stage/stateful-application-stack';

function synthesisMessageToString(sm: SynthesisMessage): string {
  return `${sm.entry.data} [${sm.id}]`;
}

describe('cdk-nag-stateless-toolchain-stack', () => {
  const app = new App({});

  // You should configure all stack (stateless, stateful) to be tested
  const statelessApplicationStack = new StatelessApplicationStack(
    app,
    'StatelessApplicationStack',
    getStatelessApplicationProps()
  );

  Aspects.of(statelessApplicationStack).add(new AwsSolutionsChecks());
  applyNagSuppression(statelessApplicationStack);

  test(`cdk-nag AwsSolutions Pack errors`, () => {
    const errors = Annotations.fromStack(statelessApplicationStack)
      .findError('*', Match.stringLikeRegexp('AwsSolutions-.*'))
      .map(synthesisMessageToString);
    expect(errors).toHaveLength(0);
  });

  test(`cdk-nag AwsSolutions Pack warnings`, () => {
    const warnings = Annotations.fromStack(statelessApplicationStack)
      .findWarning('*', Match.stringLikeRegexp('AwsSolutions-.*'))
      .map(synthesisMessageToString);
    expect(warnings).toHaveLength(0);
  });
});

describe('cdk-nag-stateful-toolchain-stack', () => {
  const app = new App({});

  // You should configure all stack (stateless, stateful) to be tested
  const statefulApplicationStack = new StatefulApplicationStack(
    app,
    'StatefulApplicationStack',
    getStatefulApplicationProps()
  );

  Aspects.of(statefulApplicationStack).add(new AwsSolutionsChecks());
  applyNagSuppression(statefulApplicationStack);

  test(`cdk-nag AwsSolutions Pack errors`, () => {
    const errors = Annotations.fromStack(statefulApplicationStack)
      .findError('*', Match.stringLikeRegexp('AwsSolutions-.*'))
      .map(synthesisMessageToString);
    expect(errors).toHaveLength(0);
  });

  test(`cdk-nag AwsSolutions Pack warnings`, () => {
    const warnings = Annotations.fromStack(statefulApplicationStack)
      .findWarning('*', Match.stringLikeRegexp('AwsSolutions-.*'))
      .map(synthesisMessageToString);
    expect(warnings).toHaveLength(0);
  });
});

/**
 * apply nag suppression
 * @param stack
 */
function applyNagSuppression(stack: Stack) {
  // These are example suppressions for this stack and should be removed and replaced with the
  // service-specific suppressions of your app.
  NagSuppressions.addStackSuppressions(
    stack,
    [{ id: 'AwsSolutions-S10', reason: 'not require requests to use SSL' }],
    true
  );
  NagSuppressions.addStackSuppressions(
    stack,
    [{ id: 'AwsSolutions-S1', reason: 'this is an example bucket' }],
    true
  );
}
