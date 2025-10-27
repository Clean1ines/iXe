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
        const subjectsFromApi = data.subjects || [];

        // NEW: Map API subjects to the format expected by the dropdown
        // For now, let's assume the API returns subject names that can be used as pageName
        // You might need to map them to specific page identifiers like 'init', 'informatics', etc.
        // For this example, I'll use the subject name directly as the value and label.
        // If the API returns 'informatics' and 'mathematics', this works.
        // If it returns full names like 'Информатика и ИКТ', you might need a mapping.
        // For now, assuming direct mapping for simplicity.
        const mappedSubjects = subjectsFromApi.map(subject => ({
          value: subject, // NEW: Use subject name from API as value
          label: subject  // NEW: Use subject name from API as label
        }));

        // NEW: Add fallback subjects if API returns empty list or only 'informatics'
        // This is temporary until the API correctly maps page names to subjects
        // Or until we have a proper mapping between API subject names and page names
        // For now, let's just use what API provides and see what it returns.
        // If API returns ['informatics', 'mathematics'], this will use those.
        // The frontend will navigate to /quiz/informatics, /quiz/mathematics etc.
        // And the API endpoint /quiz/daily/start should handle those page_names.

        // For the initial run, if API only has 'informatics' data, it might return ['informatics']
        // And the frontend will navigate to /quiz/informatics
        // The startDailyQuiz function will send POST /api/quiz/daily/start with {"page_name": "informatics"}
        // The API endpoint should then filter problems by subject 'informatics'.

        // Let's add some default subjects as fallback if API returns nothing
        // This is not ideal but ensures the UI doesn't break if API doesn't return expected subjects
        // A better approach is to ensure the API always returns a meaningful list based on DB content.
        // For now, let's assume the API will return the subjects found in the loaded DB.
        // If the loaded DB is for 'informatics', then API.get_all_problems will return problems with subject 'informatics'.
        // The get_available_subjects endpoint will return ['informatics'].
        // So, the UI will show 'informatics' as an option.
        // If user clicks start quiz for 'informatics', it goes to /quiz/informatics.
        // startDailyQuiz sends {"page_name": "informatics"}.
        // start_daily_quiz endpoint should filter by subject 'informatics'.
        // This should work if the Problem model's subject field is correctly populated during scraping.

        setAvailableSubjects(mappedSubjects);
        if (mappedSubjects.length > 0) {
          setSelectedSubject(mappedSubjects[0].value); // NEW: Set default to first available
        }
      } catch (err) {
        console.error("Ошибка при получении списка предметов:", err);
        setError(err instanceof Error ? err.message : 'Неизвестная ошибка');
        // NEW: Fallback to default subjects if API fails
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
  }, []); // NEW: Fetch subjects on component mount

  const handleStartQuiz = () => {
    // NEW: Navigate to the selected subject's quiz page
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

      {/* Здесь можно добавить другие действия в будущем */}
      {/* <div className="other-actions">
        <h2>Другие действия</h2>
        <button onClick={() => navigate('/stats')}>Статистика</button>
        <button onClick={() => navigate('/plan')}>Учебный план</button>
      </div> */}
    </div>
  );
};

export default MainPage;
