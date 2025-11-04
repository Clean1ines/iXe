def extract_task_id_and_form_id(problem_id: str) -> tuple[str, str]:
    """
    Извлекает task_id и form_id из problem_id.

    Args:
        problem_id: Идентификатор задачи из базы данных (например, 'init_4CBD4E').

    Returns:
        Кортеж (task_id, form_id), где task_id - суффикс problem_id,
        а form_id - 'q' + task_id.
    """
    # Разделяем problem_id по первому вхождению '_'
    parts = problem_id.split('_', 1)
    if len(parts) != 2:
        raise ValueError(f"Invalid problem_id format: {problem_id}")
    # task_id - это суффикс после префикса
    task_id = parts[1]
    # form_id - это 'q' + task_id
    form_id = f"q{task_id}"
    return task_id, form_id
