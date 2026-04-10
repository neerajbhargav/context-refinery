"""
ContextRefinery — Persistence Layer
Manages SQLite database for project metadata and refinement history.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import settings

logger = logging.getLogger(__name__)

class PersistenceManager:
    """Manages SQLite persistence for the application."""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or (settings.DATA_DIR / "context_refinery.db")
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Initialize the database schema."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Projects table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    root_path TEXT NOT NULL,
                    collection_name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_indexed_at TIMESTAMP
                )
            """)
            
            # Refinery history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS refinery_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT,
                    goal TEXT NOT NULL,
                    refined_prompt TEXT NOT NULL,
                    token_count INTEGER,
                    target_model TEXT,
                    eval_scores TEXT, -- JSON string
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (project_id) REFERENCES projects (id)
                )
            """)
            
            conn.commit()
        logger.info(f"Persistence layer initialized at {self.db_path}")

    # ── Project Management ──────────────────────────────────────────

    def save_project(self, id: str, name: str, root_path: str, collection_name: str):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO projects (id, name, root_path, collection_name, last_indexed_at)
                VALUES (?, ?, ?, ?, ?)
            """, (id, name, root_path, collection_name, datetime.now().isoformat()))
            conn.commit()

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def list_projects(self) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects ORDER BY last_indexed_at DESC")
            return [dict(row) for row in cursor.fetchall()]

    # ── History Management ──────────────────────────────────────────

    def add_history(self, project_id: Optional[str], goal: str, refined_prompt: str, 
                   token_count: int, target_model: str, eval_scores: Dict[str, Any]):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO refinery_history 
                (project_id, goal, refined_prompt, token_count, target_model, eval_scores)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (project_id, goal, refined_prompt, token_count, target_model, json.dumps(eval_scores)))
            conn.commit()

    def get_history(self, project_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM refinery_history 
                WHERE project_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (project_id, limit))
            return [dict(row) for row in cursor.fetchall()]

# Singleton instance
db = PersistenceManager()
