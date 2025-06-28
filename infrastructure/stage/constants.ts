import * as path from 'path';

// Dir constants
export const APP_ROOT = path.join(__dirname, '../../', 'app');
export const LAMBDA_ROOT = path.join(APP_ROOT, 'lambdas');
export const STEP_FUNCTIONS_ROOT = path.join(APP_ROOT, 'step-functions-templates');
export const LAYERS_ROOT = path.join(APP_ROOT, 'layers');

// Table constants
export const FASTQ_SYNC_TASK_TOKEN_TABLE_NAME = 'FastqSyncTaskTokenTable';

// Event constants
export const FASTQ_SYNC_LEGACY_EVENT_DETAIL_TYPE = 'fastqSync';
export const FASTQ_SYNC_EVENT_DETAIL_TYPE = 'FastqSync';

// External events to listen to
export const FASTQ_LIST_ROW_STATE_CHANGE_EVENT_DETAIL_TYPE = 'FastqListRowStateChange';
export const FASTQ_MANAGER_EVENT_SOURCE = 'orcabus.fastqmanager';

export const FASTQ_UNARCHIVING_JOB_EVENT_DETAIL_TYPE = 'FastqUnarchivingJobStateChange';
export const FASTQ_UNARCHIVING_MANAGER_EVENT_SOURCE = 'orcabus.fastqunarchivingmanager';
