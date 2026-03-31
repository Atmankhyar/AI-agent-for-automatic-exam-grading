export interface User {
  id: string;
  email: string;
  role: string;
  full_name?: string | null;
}

export interface Me {
  id: string;
  email: string;
  role: string;
  full_name?: string | null;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface Classroom {
  id: string;
  name: string;
  description?: string | null;
  owner_id: string;
}

export interface Student {
  id: string;
  email: string;
  full_name?: string | null;
}

export interface Question {
  id: string;
  type: string;
  prompt: string;
  choices?: unknown;
  answer_key?: unknown;
  rubric_json?: unknown;
  max_points: number;
  order: number;
}

export interface Exam {
  id: string;
  title: string;
  description?: string | null;
  owner_id: string;
  class_id?: string | null;
  class_name?: string | null;
  manual_statement?: string | null;
  statement_file_uri?: string | null;
  statement_text?: string | null;
  correction_file_uri?: string | null;
  correction_text?: string | null;
  config_json?: unknown;
  questions: Question[];
}

export interface Submission {
  id: string;
  exam_id: string;
  class_id?: string | null;
  class_name?: string | null;
  exam_title?: string | null;
  student_id?: string;
  student_email?: string | null;
  file_uri: string;
  status: "pending" | "processing" | "done" | "error";
  parsed_json?: unknown;
}

export interface ScoreItemFeedback {
  correction?: string;
  reponse_etudiant?: string;
  reponse_attendue?: string;
  feedback?: string;
  plagiarism?: {
    ratio: number;
    other_submission_id?: string;
    other_student_id?: string | null;
  };
}

export interface ScoreItem {
  id: string;
  question_id: string;
  points: number;
  feedback?: string | ScoreItemFeedback;
}

export interface Score {
  id: string;
  submission_id: string;
  total: number;
  breakdown?: Record<string, { points: number; feedback?: string }>;
  feedback?: unknown;
  items: ScoreItem[];
}

export interface ClassScoreItem {
  submission_id: string;
  exam_id: string;
  exam_title: string;
  class_id?: string | null;
  class_name?: string | null;
  student_id?: string | null;
  student_email?: string | null;
  total: number;
}
