/**
 * Тип для ответа на старт квиза
 */
export interface StartQuizResponse {
  quiz_id: string;
  items: QuizItem[];
}

/**
 * Тип для элемента квиза
 */
export interface QuizItem {
  problem_id: string;
  prompt: string;
  form_id: string;
}

/**
 * Тип для запроса проверки ответа
 */
export interface CheckAnswerRequest {
  quiz_id: string;
  problem_id: string;
  user_answer: string;
  form_id: string;
}

/**
 * Тип для ответа на проверку ответа
 */
export interface CheckAnswerResponse {
  verdict: 'correct' | 'incorrect';
  explanation?: string;
}

/**
 * Тип для элемента запроса завершения квиза
 */
export interface FinishQuizRequestItem {
  problem_id: string;
  user_answer: string;
  verdict: 'correct' | 'incorrect';
}

/**
 * Тип для запроса завершения квиза
 */
export interface FinishQuizRequest {
  quiz_id: string;
  results: FinishQuizRequestItem[];
}

/**
 * Тип для ответа на завершение квиза
 */
export interface FinishQuizResponse {
  success: boolean;
}

/**
 * Тип для запроса генерации учебного плана
 */
export interface GeneratePlanRequest {
  quiz_id: string;
  incorrect_problems: string[];
}

/**
 * Тип для ответа на генерацию учебного плана
 */
export interface GeneratePlanResponse {
  plan: string;
}
