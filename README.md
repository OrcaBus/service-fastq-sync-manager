Fastq Sync Manager
================================================================================

- [Service Description](#service-description)
  - [Events Overview](#events-overview)
  - [Consumed Events](#consumed-events)
    - [Legacy Method](#legacy-method)
    - [New Method(s)](#new-methods)
  - [Change Management](#change-management)
    - [Release management](#release-management)
- [Infrastructure \& Deployment](#infrastructure--deployment)
  - [Stateful](#stateful)
  - [Stateless](#stateless)
  - [CDK Commands](#cdk-commands)
  - [Stacks](#stacks)
- [Development](#development)
  - [Project Structure](#project-structure)
  - [Setup](#setup)
    - [Requirements](#requirements)
    - [Install Dependencies](#install-dependencies)
    - [First Steps](#first-steps)
  - [Conventions](#conventions)
  - [Linting \& Formatting](#linting--formatting)
  - [Testing](#testing)
- [Glossary \& References](#glossary--references)



Service Description
--------------------------------------------------------------------------------

The fastq sync service is a valuable component of the OrcaBus platform, particularly for workflow orchestration services.

The service allows other step functions across the platform to 'hang' at a certain point in their execution,
waiting for primary data to be available in a specific capacity before proceeding with their workflow.

This can include -
  * waiting for a fastq id to be restored from archive
  * waiting for a fastq id to contain a valid read set
  * waiting for a fastq id to contain qc data

This is particularly useful for services that need to wait for external events or conditions before
proceeding with their workflow.


### Events Overview

![Fastq Sync Service Events](./docs/draw-io-exports/fastq-sync.drawio.svg)


### Consumed Events

| Name / DetailType                | Source                     | Schema Link                                                                 | Description         |
|----------------------------------|----------------------------|-----------------------------------------------------------------------------|---------------------|
| `FastqSync`                      | `any`                      | [fastq-sync-request](./event-schemas/fastq-sync-request-list.schema.json)  | Announces service state changes |
| `FastqListRowStateChange`        | `orcabus.fastqmanager`     | <schema link  // TODO>                                                      | Announces service state changes |
| `FastqUnarchivingJobStateChange` | `orcabus.fastqunarchiving` | <schema link  // TODO >                                                     | Announces service state changes |


#### Legacy Method

```json5
{
  "EventBusName": "OrcaBusMain",
  "Source": "any",
  // Note detail type value is in camelCase
  "DetailType": "fastqSync",
  "Detail": {
    // Task Token
    "taskToken": "string",
    // Supports only a single fastq set id
    "fastqSetId": "fqs.12345",
    "requirements": {
      "hasActiveReadSet": true,
      // Other requirements
    },
    "forceUnarchiving": true
  }
}
```


#### New Method(s)

Now we use two new methods to handle fastq sync requests:

**FastqIdList**

```json5
{
  "EventBusName": "OrcaBusMain",
  "Source": "any",
  // Note detail type value is now in PascalCase
  // Which is consistent with the rest of the platform
  "DetailType": "FastqSync",
  "Detail": {
    // Task Token
    "taskToken": "string",
    // Payload
    // All other keys are now under the `payload` key
    "payload": {
      // Supports a list of fastq ids
      "fastqIdList": [
        "fqr.12345",
        "fqr.67890"
      ],
      "requirements": {
        "hasActiveReadSet": true,
        // ...
      },
      "forceUnarchiving": true
    }
  }
}
```

**FastqSetIdList**

```json5
{
  "EventBusName": "OrcaBusMain",
  "Source": "any",
  // Note detail type value is now in PascalCase
  // Which is consistent with the rest of the platform
  "DetailType": "FastqSync",
  "Detail": {
    // Task Token
    "taskToken": "string",
    // Payload
    // All other keys are now under the `payload` key
    "payload": {
      // Supports a list of fastq set ids
      "fastqSetIdList": [
        "fqs.12345",
        "fqs.67890"
      ],
      "requirements": {
        "hasActiveReadSet": true,
        // ...
      },
      "forceUnarchiving": true
    }
  }
}
```

### Change Management

#### Release management

The service employs a fully automated CI/CD pipeline that automatically builds and releases all changes to the `main` code branch.


Infrastructure & Deployment
--------------------------------------------------------------------------------

Short description with diagrams where appropriate.
Deployment settings / configuration (e.g. CodePipeline(s) / automated builds).

Infrastructure and deployment are managed via CDK. This template provides two types of CDK entry points: `cdk-stateless` and `cdk-stateful`.


### Stateful

- Queues
- Buckets
- Database
- ...

### Stateless
- Lambdas
- StepFunctions


### CDK Commands

You can access CDK commands using the `pnpm` wrapper script.

- **`cdk-stateless`**: Used to deploy stacks containing stateless resources (e.g., AWS Lambda), which can be easily redeployed without side effects.
- **`cdk-stateful`**: Used to deploy stacks containing stateful resources (e.g., AWS DynamoDB, AWS RDS), where redeployment may not be ideal due to potential side effects.

The type of stack to deploy is determined by the context set in the `./bin/deploy.ts` file. This ensures the correct stack is executed based on the provided context.

For example:

```sh
# Deploy a stateless stack
pnpm cdk-stateless <command>

# Deploy a stateful stack
pnpm cdk-stateful <command>
```

### Stacks

This CDK project manages multiple stacks. The root stack (the only one that does not include `DeploymentPipeline` in its stack ID) is deployed in the toolchain account and sets up a CodePipeline for cross-environment deployments to `beta`, `gamma`, and `prod`.

To list all available stacks, run:

```sh
pnpm cdk-stateless ls
```

Example output:

```sh
OrcaBusStatelessServiceStack
OrcaBusStatelessServiceStack/DeploymentPipeline/OrcaBusBeta/DeployStack (OrcaBusBeta-DeployStack)
OrcaBusStatelessServiceStack/DeploymentPipeline/OrcaBusGamma/DeployStack (OrcaBusGamma-DeployStack)
OrcaBusStatelessServiceStack/DeploymentPipeline/OrcaBusProd/DeployStack (OrcaBusProd-DeployStack)
```


Development
--------------------------------------------------------------------------------

### Project Structure

The root of the project is an AWS CDK project where the main application logic lives inside the `./app` folder.

The project is organized into the following key directories:

- **`./app`**: Contains the main application logic. You can open the code editor directly in this folder, and the application should run independently.

- **`./bin/deploy.ts`**: Serves as the entry point of the application. It initializes two root stacks: `stateless` and `stateful`. You can remove one of these if your service does not require it.

- **`./infrastructure`**: Contains the infrastructure code for the project:
  - **`./infrastructure/toolchain`**: Includes stacks for the stateless and stateful resources deployed in the toolchain account. These stacks primarily set up the CodePipeline for cross-environment deployments.
  - **`./infrastructure/stage`**: Defines the stage stacks for different environments:
    - **`./infrastructure/stage/config.ts`**: Contains environment-specific configuration files (e.g., `beta`, `gamma`, `prod`).
    - **`./infrastructure/stage/stack.ts`**: The CDK stack entry point for provisioning resources required by the application in `./app`.

- **`.github/workflows/pr-tests.yml`**: Configures GitHub Actions to run tests for `make check` (linting and code style), tests defined in `./test`, and `make test` for the `./app` directory. Modify this file as needed to ensure the tests are properly configured for your environment.

- **`./test`**: Contains tests for CDK code compliance against `cdk-nag`. You should modify these test files to match the resources defined in the `./infrastructure` folder.


### Setup

#### Requirements

```sh
node --version
v22.9.0

# Update Corepack (if necessary, as per pnpm documentation)
npm install --global corepack@latest

# Enable Corepack to use pnpm
corepack enable pnpm

```

#### Install Dependencies

To install all required dependencies, run:

```sh
make install
```

#### First Steps

Before using this template, search for all instances of `TODO:` comments in the codebase and update them as appropriate for your service. This includes replacing placeholder values (such as stack names).


### Conventions

### Linting & Formatting

Automated checks are enforces via pre-commit hooks, ensuring only checked code is committed. For details consult the `.pre-commit-config.yaml` file.

Manual, on-demand checking is also available via `make` targets (see below). For details consult the `Makefile` in the root of the project.


To run linting and formatting checks on the root project, use:

```sh
make check
```

To automatically fix issues with ESLint and Prettier, run:

```sh
make fix
```

### Testing


Unit tests are available for most of the business logic. Test code is hosted alongside business in `/tests/` directories.

```sh
make test
```

Glossary & References
--------------------------------------------------------------------------------

For general terms and expressions used across OrcaBus services, please see the platform [documentation](https://github.com/OrcaBus/wiki/blob/main/orcabus-platform/README.md#glossary--references).

Service specific terms:

| Term      | Description                                      |
|-----------|--------------------------------------------------|
| Foo | ... |
| Bar | ... |
