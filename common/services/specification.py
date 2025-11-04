"""
Service for loading and querying official FIPI specifications (KES/KOS).
Provides human-readable explanations for exam codes and task metadata.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any

class SpecificationService:
    def __init__(self, spec_path: Path, kes_kos_path: Path):
        """
        Initialize with paths to official FIPI JSON specifications.
        
        Args:
            spec_path: Path to e.g. ege_2026_math_spec.json
            kes_kos_path: Path to e.g. ege_2026_math_kes_kos.json
        """
        self.spec = self._load_json(spec_path)
        self.kes_kos_map = {item["kes_code"]: item for item in self._load_json(kes_kos_path)["mapping"]}
    
    def _load_json(self, path: Path) -> Any:
        """Helper to load JSON safely."""
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def get_task_spec(self, task_number: int) -> Optional[Dict]:
        """Get official task specification by number (1–19)."""
        for task in self.spec.get("tasks", []):
            if task.get("task_number") == task_number:
                return task
        return None
    
    def explain_kos(self, kos_code: str) -> str:
        """Return human-readable KOS description."""
        # Find first entry with matching KOS code
        for item in self.kes_kos_map.values():
            if item.get("kos_code") == kos_code:
                return item.get("kos_description", f"Описание для КОС {kos_code} не найдено")
        return f"КОС {kos_code} не найден в спецификации"
    
    def explain_kes(self, kes_code: str) -> str:
        """Return human-readable KES description."""
        item = self.kes_kos_map.get(kes_code)
        if item:
            return f"{kes_code} — {item.get('kes_description', '')}"
        return f"КЭС {kes_code} не найден"
    
    def get_feedback_for_task(self, task_number: int) -> Dict[str, Any]:
        """
        Generate pedagogical feedback for a given task number.
        Returns structured feedback including KOS explanation, KES topics, and next steps.
        """
        task = self.get_task_spec(task_number)
        if not task:
            return {
                "kos_explanation": "Задание не найдено в спецификации",
                "kes_topics": [],
                "next_steps": ["Обратитесь к преподавателю"]
            }
        
        kos_codes = task.get("kos_codes", [])
        kes_codes = task.get("kes_codes", [])
        
        # Use first KOS for explanation (typically most relevant)
        kos_explanation = self.explain_kos(kos_codes[0]) if kos_codes else "Требования не указаны"
        
        # Format KES topics
        kes_topics = [self.explain_kes(code) for code in kes_codes]
        
        # Basic next steps (can be enhanced with adaptive logic later)
        next_steps = [
            "Повторите соответствующий раздел теории",
            f"Решите 3 дополнительные задачи по теме '{task.get('description', '')[:30]}...'"
        ]
        
        return {
            "kos_explanation": kos_explanation,
            "kes_topics": kes_topics,
            "next_steps": next_steps
        }
