export type TestCase = {
  input: unknown[];
  output: unknown;
};

export type Problem = {
  uuid: string;
  title: string;
  statement: string;
  hints: string | null;
  examples: string | null;
  test_cases: TestCase[] | null;
  function_signature: string | null;
  created_at: string;
};

export type ProblemOption = {
  uuid: string;
  title: string;
  function_signature: string | null;
};

export type QueueEntrySummary = {
  uuid: string;
  attempt_count: number;
  last_checked_at: string | null;
  last_error: string | null;
  created_at: string;
};

export type EvaluationDetail = {
  uuid: string;
  success: boolean;
  metadata_: Record<string, unknown> | null;
  created_at: string;
};

export type Submission = {
  uuid: string;
  artifact_uri: string;
  problem_uuid: string;
  created_at: string;
  runs: RunSummary[];
  queue_entries: QueueEntrySummary[];
  evaluations: EvaluationDetail[];
};

export type SubmissionSummary = {
  uuid: string;
  artifact_uri: string;
  problem_uuid: string;
  created_at: string;
};

export type RunSummary = {
  uuid: string;
  status: string;
  execution_ref: string | null;
  failure_stage: string | null;
  failure_error: string | null;
  runner_output_uri: string | null;
  grader_output_uri: string | null;
  created_at: string;
};

export type RunEntry = {
  uuid: string;
  submission_uuid: string;
  status: string;
  execution_ref: string | null;
  failure_stage: string | null;
  failure_error: string | null;
  runner_output_uri: string | null;
  grader_output_uri: string | null;
  created_at: string;
};

export type EvaluationSummary = {
  uuid: string;
  success: boolean;
  created_at: string;
};

export type QueueEntry = {
  uuid: string;
  submission_uuid: string;
  problem_uuid: string;
  attempt_count: number;
  last_checked_at: string | null;
  last_error: string | null;
  created_at: string;
  runs: RunSummary[];
  evaluations: EvaluationSummary[];
};
