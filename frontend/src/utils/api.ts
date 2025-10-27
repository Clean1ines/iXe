import {
  StartQuizResponse,
  CheckAnswerRequest,
  CheckAnswerResponse,
  FinishQuizRequestItem,
  FinishQuizRequest,
  FinishQuizResponse,
  GeneratePlanRequest,
  GeneratePlanResponse
} from '../types/api';

// NEW: Update API_BASE_URL to use the proxy path on your domain
const API_BASE_URL = '/api'; // Changed from 'http://localhost:8001'

/**
 * Начинает ежедневный квиз для указанной страницы
 * @param pageName - имя страницы для квиза
 * @returns Promise с ответом от сервера
 * @throws Ошибка при неудачном запросе
 */
export async function startDailyQuiz(pageName?: string): Promise<StartQuizResponse> {
  // NEW: Construct URL using the proxy path
  const url = pageName ? `${API_BASE_URL}/quiz/daily/start?page_name=${encodeURIComponent(pageName)}` : `${API_BASE_URL}/quiz/daily/start`;
  const response = await fetch(url, {
    method: 'POST', // NEW: Changed from GET to POST as per API spec
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Ошибка при запуске квиза: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Отправляет ответ пользователя на проверку
 * @param data - данные для проверки ответа
 * @returns Promise с результатом проверки
 * @throws Ошибка при неудачном запросе
 */
export async function submitAnswer(data: CheckAnswerRequest): Promise<CheckAnswerResponse> {
  // NEW: Use the proxy path for answer endpoint too
  const response = await fetch(`${API_BASE_URL}/answer`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Ошибка при отправке ответа: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Завершает квиз с результатами
 * @param quizId - идентификатор квиза
 * @param results - результаты задач
 * @returns Promise с результатом завершения
 * @throws Ошибка при неудачном запросе
 */
export async function finishQuiz(quizId: string, results: FinishQuizRequestItem[]): Promise<FinishQuizResponse> {
  // NEW: Use the proxy path for finish endpoint too
  const response = await fetch(`${API_BASE_URL}/quiz/finish`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      quiz_id: quizId,
      results: results
    } as FinishQuizRequest),
  });

  if (!response.ok) {
    throw new Error(`Ошибка при завершении квиза: ${response.status} ${response.statusText}`);
  }

  return response.json();
}

/**
 * Генерирует учебный план на основе неправильных ответов
 * @param data - данные для генерации плана
 * @returns Promise с сгенерированным планом
 * @throws Ошибка при неудачном запросе
 */
export async function generateStudyPlan(data: GeneratePlanRequest): Promise<GeneratePlanResponse> {
  // NEW: Use the proxy path for plan generation endpoint too
  const response = await fetch(`${API_BASE_URL}/plan/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error(`Ошибка при генерации плана: ${response.status} ${response.statusText}`);
  }

  return response.json();
}
