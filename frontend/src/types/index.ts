export interface Problem {
  id: string;
  subject: 'math' | 'informatics' | 'russian';
  question: string;
  options?: string[];
  correctAnswer: string | number;
  explanation?: string;
}

export interface UserProgress {
  problemId: string;
  userAnswer: string | number;
  isCorrect: boolean;
  timestamp: number;
}
