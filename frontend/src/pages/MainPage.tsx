import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

/**
 * Главная страница приложения
 * Предоставляет выбор действия: начать квиз по предмету
 */
const MainPage: React.FC = () => {
  const navigate = useNavigate();
  const [selectedSubject, setSelectedSubject] = useState<string>('init'); // По умолчанию 'init' для математики, если список пуст
  const [availableSubjects, setAvailableSubjects] = useState<{ value: string; label: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSubjects = async () => {
      try {
        setLoading(true);
        const response = await fetch('/api/subjects/available'); // NEW: Fetch subjects from API
        if (!response.ok) {
          throw new Error(`Ошибка получения предметов: ${response.status} ${response.statusText}`);
        }
        const data = await response.json();
        const subjectsFromApi: string[] = data.subjects || [];

        // NEW: Map API subjects to the format expected by the dropdown
        const mappedSubjects = subjectsFromApi.map((subject: string) => ({
          value: subject,
          label: subject
        }));

        setAvailableSubjects(mappedSubjects);
        if (mappedSubjects.length > 0) {
          setSelectedSubject(mappedSubjects[0].value);
        }
      } catch (err) {
        console.error("Ошибка при получении списка предметов:", err);
        setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
        // Fallback subjects
        setAvailableSubjects([
          { value: 'init', label: 'ЕГЭ Математика' },
          { value: 'informatics', label: 'ЕГЭ Информатика' },
          { value: 'russian', label: 'ЕГЭ Русский язык' },
        ]);
        setSelectedSubject('init');
      } finally {
        setLoading(false);
      }
    };

    fetchSubjects();
  }, []);

  const handleStartQuiz = () => {
    navigate(`/quiz/${selectedSubject}`);
  };

  if (loading) {
    return <div>Загрузка списка предметов...</div>;
  }

  if (error) {
    return <div>Ошибка загрузки предметов: {error}</div>;
  }

  return (
    <div className="main-page">
      <h1>Добро пожаловать в Quiz App</h1>
      <p>Выберите предмет для начала квиза:</p>
      
      <div className="subject-selector">
        <select 
          value={selectedSubject} 
          onChange={(e) => setSelectedSubject(e.target.value)}
          className="subject-dropdown"
        >
          {availableSubjects.map(subject => (
            <option key={subject.value} value={subject.value}>
              {subject.label}
            </option>
          ))}
        </select>
        
        <button onClick={handleStartQuiz} className="start-button">
          Начать квиз
        </button>
      </div>
    </div>
  );
};

export default MainPage;
