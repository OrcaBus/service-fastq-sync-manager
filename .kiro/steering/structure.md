# Project Structure

```
.
├── bin/
│   └── deploy.ts                  # CDK app entry point (selects stateful/stateless via context)
├── infrastructure/
│   ├── toolchain/                 # CodePipeline stacks (deployed to toolchain account)
│   │   ├── stateless-stack.ts
│   │   └── stateful-stack.ts
│   └── stage/                     # Application stacks (deployed per environment)
│       ├── config.ts              # Environment-specific configuration
│       ├── constants.ts           # Shared constants (paths, names, durations)
│       ├── interfaces.ts          # TypeScript interfaces for stack props
│       ├── stateful-application-stack.ts
│       ├── stateless-application-stack.ts
│       ├── dynamodb/              # DynamoDB table constructs
│       ├── event-rules/           # EventBridge rule definitions
│       ├── event-targets/         # EventBridge target bindings
│       ├── lambdas/               # Lambda CDK construct builders
│       ├── sqs/                   # SQS queue constructs
│       ├── step-functions/        # Step Function CDK construct builders
│       └── utils/                 # Shared infra utilities
├── app/                           # Application logic (independent of CDK)
│   ├── event-schemas/             # JSON Schema files for events
│   ├── lambdas/                   # Python Lambda handlers
│   │   └── <handler_name>_py/    # Each lambda in its own directory
│   │       ├── <handler_name>.py
│   │       └── requirements.txt   # (optional, per-lambda deps)
│   ├── layers/                    # Shared Lambda layers
│   │   └── fastq_sync_tools_layer/
│   │       ├── pyproject.toml     # Poetry-managed Python deps
│   │       └── src/fastq_sync_tools/
│   └── step-functions-templates/  # ASL JSON state machine definitions
├── test/                          # CDK compliance tests (cdk-nag)
├── docs/                          # Documentation and diagrams
└── .github/workflows/             # CI pipeline (PR tests)
```

## Key Patterns

### Dual-Stack Architecture

The project separates **stateful** (DynamoDB, SQS queues) and **stateless** (Lambdas, Step Functions) resources into independent CDK stacks. This allows safe redeployment of compute resources without risking data stores.

### Lambda Organization

Each Lambda lives in `app/lambdas/<name>_py/` with a Python file matching the directory name. The `_py` suffix signals the runtime to CDK construct builders.

### Shared Layer

Common utilities live in `app/layers/fastq_sync_tools_layer/` and are packaged as a Lambda Layer. Dependencies are managed via Poetry.

### Step Functions as ASL Templates

State machines are defined as ASL JSON files in `app/step-functions-templates/` and referenced by CDK constructs that wire in Lambda ARNs and other resource references.

### Infrastructure Sub-Modules

The `infrastructure/stage/` directory is modular — each AWS resource type (lambdas, step-functions, event-rules, etc.) has its own subdirectory with builder functions that the main stack composes together.

### Event-Driven Composition

The stack wires resources in a clear order: EventBridge rules → targets → Step Functions → Lambdas → DynamoDB/SQS. Each layer is built by a dedicated builder function and composed in the stateless stack.
