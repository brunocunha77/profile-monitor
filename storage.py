"""Persistence for Profile Monitor: local JSON by default, database when configured."""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urlparse


def default_state() -> dict:
    return {
        'connection': {'status': 'not_configured', 'last_error': None, 'updated_at': datetime.now(timezone.utc).isoformat()},
        'targets': [], 'run': None, 'signals': [], 'prospect_statuses': {}, 'lead_ids': {},
    }


class StateStore:
    """Keeps one monitor workspace in a JSON file or a database JSON document."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.database_url = os.getenv('DATABASE_URL', '').strip()
        self.workspace_id = os.getenv('MONITOR_WORKSPACE_ID', 'local').strip() or 'local'
        self.file_path = root / 'state' / 'control.json'
        self.mode = 'database' if self.database_url else 'local'
        if self.database_url:
            self._initialize_database()

    def load(self) -> dict:
        if not self.database_url:
            if self.file_path.exists():
                return self._normalize(json.loads(self.file_path.read_text(encoding='utf-8')))
            return default_state()
        return self._normalize(self._database_load())

    def save(self, state: dict) -> None:
        state = self._normalize(state)
        if not self.database_url:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            self.file_path.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding='utf-8')
            return
        self._database_save(state)

    @staticmethod
    def _normalize(state: dict) -> dict:
        base = default_state()
        for key, value in base.items():
            state.setdefault(key, value)
        return state

    def _sqlite_path(self) -> Path:
        parsed = urlparse(self.database_url)
        if parsed.scheme != 'sqlite':
            raise ValueError('Not a SQLite URL')
        path = unquote(parsed.path)
        if path.startswith('/') and self.database_url.startswith('sqlite:///'):
            path = path[1:]
        return Path(path)

    def _initialize_database(self) -> None:
        if self.database_url.startswith('sqlite:'):
            path = self._sqlite_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(path) as conn:
                conn.execute('CREATE TABLE IF NOT EXISTS profile_monitor_state (workspace_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL)')
            return
        if self.database_url.startswith(('postgres://', 'postgresql://')):
            try:
                import psycopg
            except ImportError as error:
                raise RuntimeError('Para PostgreSQL, instale as dependências com: python -m pip install -r collector/requirements.txt') from error
            with psycopg.connect(self.database_url) as conn:
                conn.execute('CREATE TABLE IF NOT EXISTS profile_monitor_state (workspace_id TEXT PRIMARY KEY, payload JSONB NOT NULL, updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW())')
            return
        raise RuntimeError('DATABASE_URL deve começar com sqlite:/// ou postgresql://')

    def _database_load(self) -> dict:
        if self.database_url.startswith('sqlite:'):
            with sqlite3.connect(self._sqlite_path()) as conn:
                row = conn.execute('SELECT payload FROM profile_monitor_state WHERE workspace_id = ?', (self.workspace_id,)).fetchone()
            return json.loads(row[0]) if row else default_state()
        import psycopg
        with psycopg.connect(self.database_url) as conn:
            row = conn.execute('SELECT payload FROM profile_monitor_state WHERE workspace_id = %s', (self.workspace_id,)).fetchone()
        return row[0] if row else default_state()

    def _database_save(self, state: dict) -> None:
        payload = json.dumps(state, ensure_ascii=True)
        if self.database_url.startswith('sqlite:'):
            with sqlite3.connect(self._sqlite_path()) as conn:
                conn.execute('INSERT INTO profile_monitor_state (workspace_id, payload, updated_at) VALUES (?, ?, ?) ON CONFLICT(workspace_id) DO UPDATE SET payload=excluded.payload, updated_at=excluded.updated_at', (self.workspace_id, payload, datetime.now(timezone.utc).isoformat()))
            return
        import psycopg
        with psycopg.connect(self.database_url) as conn:
            conn.execute('INSERT INTO profile_monitor_state (workspace_id, payload, updated_at) VALUES (%s, %s::jsonb, NOW()) ON CONFLICT(workspace_id) DO UPDATE SET payload=excluded.payload, updated_at=NOW()', (self.workspace_id, payload))