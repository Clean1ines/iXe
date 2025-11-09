import sqlite3
import os
from pathlib import Path

DB_PATH = Path("data/fipi_data.db")

def initialize_database():
    """Initialize database with required tables if they don't exist"""
    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create problems table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS problems (
        problem_id TEXT PRIMARY KEY,
        subject TEXT NOT NULL,
        content TEXT NOT NULL,
        answer TEXT,
        answer_type TEXT NOT NULL,
        kes_codes TEXT,
        kos_codes TEXT,
        task_number INTEGER NOT NULL,
        difficulty_level TEXT NOT NULL,
        exam_part INTEGER NOT NULL,
        max_score INTEGER NOT NULL,
        metadata TEXT,
        offline_html TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create answers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        problem_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        answer_text TEXT NOT NULL,
        is_correct BOOLEAN,
        score REAL,
        feedback TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (problem_id) REFERENCES problems(problem_id)
    )
    """)
    
    # Create subjects table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS subjects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        alias TEXT NOT NULL UNIQUE,
        proj_id TEXT NOT NULL
    )
    """)
    
    # Insert default subjects
    default_subjects = [
        ("Математика", "math", "1"),
        ("Информатика", "informatics", "2"),
        ("Математика. Профильный уровень", "promath", "3")
    ]
    
    cursor.executemany("""
    INSERT OR IGNORE INTO subjects (name, alias, proj_id) VALUES (?, ?, ?)
    """, default_subjects)
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

if __name__ == "__main__":
    initialize_database()
