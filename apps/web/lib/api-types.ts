export type AuthTokens = {
  access_token: string;
  refresh_token: string;
  token_type: string;
};

export type AuthMeResponse = {
  id: string;
  email: string;
  full_name: string | null;
  role: string | null;
  created_at: string;
};

export type SubjectSummaryResponse = {
  id: string;
  name: string;
  description: string | null;
  difficulty_level: string | null;
  modules_count: number;
  topics_count: number;
  lessons_count: number;
  progress_percent: number;
};

export type LessonSummaryResponse = {
  id: string;
  title: string;
  summary: string | null;
};

export type TopicDetailResponse = {
  id: string;
  title: string;
  objective: string | null;
  difficulty: string | null;
  lessons: LessonSummaryResponse[];
};

export type ModuleDetailResponse = {
  id: string;
  title: string;
  description: string | null;
  order: number | null;
  topics: TopicDetailResponse[];
};

export type SubjectDetailResponse = SubjectSummaryResponse & {
  modules: ModuleDetailResponse[];
};

export type QuizListItemResponse = {
  id: string;
  title: string;
  mode: string | null;
  level: string | null;
  topic_id: string | null;
  topic_title: string | null;
  subject_id: string | null;
  subject_name: string | null;
  question_count: number;
  last_score: number | null;
  last_attempt_at: string | null;
};

export type QuizQuestionResponse = {
  id: string;
  question_text: string;
  choices: Record<string, string>;
  explanation: string | null;
};

export type QuizDetailResponse = QuizListItemResponse & {
  questions: QuizQuestionResponse[];
};

export type QuizAttemptSubmitRequest = {
  answers: Array<{
    question_id: string;
    selected_answer: string;
  }>;
};

export type QuizAttemptSubmitResponse = {
  attempt_id: string;
  quiz_id: string;
  score: number;
  correct_count: number;
  total_questions: number;
  completed_at: string;
  answers: Array<{
    question_id: string;
    selected_answer: string | null;
    correct_answer: string;
    is_correct: boolean;
    explanation: string | null;
  }>;
};

export type QuizAttemptHistoryItemResponse = {
  attempt_id: string;
  quiz_id: string;
  quiz_title: string;
  subject_name: string | null;
  score: number | null;
  correct_count: number;
  total_questions: number;
  completed_at: string | null;
};

export type SubjectProgressResponse = {
  subject_id: string;
  subject_name: string;
  progress_percent: number;
  average_quiz_score: number | null;
  study_minutes: number;
  completed_quizzes: number;
};

export type WeeklyTrendPointResponse = {
  date: string;
  minutes: number;
};

export type ProgressSummaryResponse = {
  weekly_minutes: number;
  weekly_hours: number;
  weekly_goal_minutes: number;
  weekly_goal_percent: number;
  average_quiz_score: number;
  completed_quizzes: number;
  completed_lessons: number;
  subject_progress: SubjectProgressResponse[];
  weekly_trend: WeeklyTrendPointResponse[];
};

export type ProgressSnapshotResponse = {
  id: string;
  subject_id: string;
  metric: Record<string, unknown>;
  captured_at: string;
};

export type StudySessionRequest = {
  subject_id?: string;
  duration_minutes: number;
  studied_at?: string;
};

export type UserProfileResponse = {
  name: string | null;
  email: string;
  role: string | null;
  track: string | null;
  interests: string[];
  avatar_url: string | null;
  locale: string | null;
  timezone: string | null;
};

export type UserProfilePatchRequest = {
  name?: string;
  email?: string;
  track?: string;
  interests?: string[];
  avatar_url?: string;
  locale?: string;
  timezone?: string;
};

export type UserPreferencesResponse = {
  email_notifications: boolean;
  weekly_report: boolean;
  daily_reminder: boolean;
  dark_mode: boolean;
  compact_view: boolean;
};

export type UserPreferencesPatchRequest = Partial<UserPreferencesResponse>;
