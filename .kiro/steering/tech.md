# Tech Stack

## Infrastructure (TypeScript)

- **AWS CDK** (v2.256+) — Infrastructure as Code
- **TypeScript** (v5.x) — CDK construct definitions
- **Node.js** (v22.x) — Runtime for CDK synthesis
- **pnpm** (v11.x, managed via Corepack) — Package manager
- **`@orcabus/platform-cdk-constructs`** — Shared OrcaBus platform CDK library

## Application (Python)

- **Python 3.14** — Lambda runtime
- **Poetry** — Python dependency management (for Lambda layers)
- **boto3** — AWS SDK
- **aws-durable-execution-sdk-python** — Durable execution / callback pattern for Lambdas

## AWS Services Used

- AWS Lambda (Python handlers)
- AWS Step Functions (orchestration via ASL JSON templates)
- Amazon EventBridge (event routing)
- Amazon DynamoDB (task token state storage)
- Amazon SQS (request queuing with throttling)
- AWS CodePipeline (CI/CD)

## Code Quality & Formatting

- **ESLint** (v10) + **typescript-eslint** — TypeScript linting
- **Prettier** — Code formatting (2-space indent, single quotes, 100 char print width, trailing commas es5)
- **pre-commit** — Git hooks for lint/format/secrets checks
- **detect-secrets** — Secret leak prevention
- **cdk-nag** — CDK compliance/best-practice tests

## Common Commands

```bash
# Install all dependencies
make install

# Run linting and formatting checks
make check

# Auto-fix lint and formatting issues
make fix

# Run tests (TypeScript compile + Jest)
make test

# CDK commands (stateless resources)
pnpm cdk-stateless synth
pnpm cdk-stateless deploy
pnpm cdk-stateless diff

# CDK commands (stateful resources)
pnpm cdk-stateful synth
pnpm cdk-stateful deploy

# List all CDK stacks
pnpm cdk-stateless ls
```

## Testing

- **Jest** (v30) + **ts-jest** — Unit tests for CDK constructs
- **cdk-nag** — Compliance tests in `./test`
- **pytest** — Python testing framework (not currently used in this repository)
- GitHub Actions CI runs `make check` and `pnpm test` on PRs
