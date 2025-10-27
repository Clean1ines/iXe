import React, { useEffect } from 'react';
import { QuizItem } from '../types/api';
import AnswerForm from './AnswerForm';

interface ProblemBlockProps {
  item: QuizItem;
  onCorrectAnswer?: () => void;
}

// Объявление типа для MathJax
declare global {
  interface Window {
    MathJax: any;
  }
}

/**
 * Компонент блока задачи, отображающий условие и форму для ответа
 * @param item - объект задачи
 * @param onCorrectAnswer - колбэк, вызываемый при правильном ответе
 */
const ProblemBlock: React.FC<ProblemBlockProps> = ({ item, onCorrectAnswer }) => {
  useEffect(() => {
    // Рендерим LaTeX формулы после обновления DOM
    if (window.MathJax && window.MathJax.typesetPromise) {
      window.MathJax.typesetPromise();
    }
  }, [item.prompt]);

  return (
    <div 
      className="problem-block" 
      data-task-id={item.problem_id} 
      data-form-id={item.form_id}
    >
      <div 
        className="problem-prompt" 
        dangerouslySetInnerHTML={{ __html: item.prompt }} 
      />
      <AnswerForm 
        problemId={item.problem_id} 
        formId={item.form_id} 
        onCorrectAnswer={onCorrectAnswer}
      />
    </div>
  );
};

export default ProblemBlock;
