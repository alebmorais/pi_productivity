"""Utilities to persist task data for the e-paper display.

The Raspberry Pi setup does not have a database yet.  This module
creates a small SQLite database with a single ``tasks`` table and
provides helpers for synchronising Motion tasks and reading a compact
summary for the e-paper widget.
"""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence

from utils import normalize_and_format_date, today_local

_DEFAULT_DB_PATH = Path(
    os.getenv("PI_PRODUCTIVITY_DB", "~/pi_productivity/data/tasks.db")
).expanduser()


def _ensure_parent(path: Path) -> None:
    """Create the parent directory for *path* if it does not exist."""

    path.parent.mkdir(parents=True, exist_ok=True)


class TaskDatabase:
    """Wrapper around the SQLite file used by the project."""

    def __init__(self, db_path: Path | str | None = None):
        self.path = Path(db_path).expanduser() if db_path else _DEFAULT_DB_PATH
        _ensure_parent(self.path)
        self._initialise()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        return conn

    def _initialise(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    task_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    subtitle TEXT,
                    due_date TEXT,
                    status TEXT,
                    raw JSON,
                    updated_at TEXT NOT NULL
                )
                """
            )

    # ------------------------------------------------------------------
    # Synchronisation helpers
    # ------------------------------------------------------------------
    def upsert_motion_tasks(self, tasks: Sequence[Mapping[str, object]]) -> int:
        """Store/refresh tasks coming from the Motion API.

        ``MotionClient`` returns a list of dictionaries.  Their shape may
        change over time, so we keep the raw payload while extracting a
        few common fields that are useful for the e-paper panel.
        """

        now = datetime.utcnow().isoformat(timespec="seconds")
        normalised = [self._normalise_task(t, now) for t in tasks]
        if not normalised:
            return 0
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT INTO tasks (task_id, title, subtitle, due_date, status, raw, updated_at)
                VALUES (:task_id, :title, :subtitle, :due_date, :status, :raw, :updated_at)
                ON CONFLICT(task_id) DO UPDATE SET
                    title = excluded.title,
                    subtitle = excluded.subtitle,
                    due_date = excluded.due_date,
                    status = excluded.status,
                    raw = excluded.raw,
                    updated_at = excluded.updated_at
                """,
                normalised,
            )
        return len(normalised)

    def _normalise_task(self, payload: Mapping[str, object], updated_at: str) -> Mapping[str, object]:
        get = payload.get
        task_id = get("id") or get("taskId") or get("uid") or get("_id")
        if task_id is None:
            task_id = hash(json.dumps(payload, sort_keys=True))
        task_id = str(task_id)

        title = (
            get("name")
            or get("title")
            or get("summary")
            or get("description")
            or "Tarefa sem nome"
        )
        title = str(title).strip() or "Tarefa sem nome"

        subtitle = self._extract_subtitle(payload)

        raw_due = (
            get("dueDate")
            or get("due")
            or get("due_date")
            or get("deadline")
            or get("end")
        )
        due_date = normalize_and_format_date(raw_due)

        status = (
            get("status")
            or ("completed" if bool(get("completed")) else "pending")
            or "pending"
        )
        status = str(status)

        return {
            "task_id": task_id,
            "title": title,
            "subtitle": subtitle,
            "due_date": due_date,
            "status": status,
            "raw": json.dumps(payload, ensure_ascii=False, default=str),
            "updated_at": updated_at,
        }

    @staticmethod
    def _extract_subtitle(payload: Mapping[str, object]) -> str:
        def _stringify(value: object) -> str:
            return str(value).strip()

        labels = payload.get("labels") or payload.get("labelNames")
        if isinstance(labels, Iterable) and not isinstance(labels, (str, bytes, dict)):
            clean = [
                _stringify(lbl)
                for lbl in labels
                if _stringify(lbl)
            ]
            if clean:
                return ", ".join(clean[:3])
        if labels:
            return _stringify(labels)

        description = payload.get("description") or payload.get("note")
        if isinstance(description, str):
            first_line = description.strip().splitlines()[0]
            if first_line:
                return first_line[:60]

        project = payload.get("projectName") or payload.get("project")
        if project:
            return _stringify(project)

        return ""

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def fetch_items_for_display(self, limit: int = 6) -> List[dict]:
        """Return a list of simplified entries for the e-paper display."""

        today = today_local()
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT task_id, title, subtitle, due_date, status
                    FROM tasks
                    WHERE COALESCE(LOWER(status), 'pending') NOT IN ('completed', 'done', 'cancelled', 'canceled', 'archived')
                    ORDER BY
                        CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,
                        due_date ASC,
                        updated_at DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
        except sqlite3.Error as exc:
            return [
                {
                    "title": "Erro ao ler tarefas",
                    "subtitle": str(exc),
                    "right": "",
                }
            ]

        if not rows:
            return [
                {
                    "title": "Sem tarefas pendentes",
                    "subtitle": "Aproveite para descansar!",
                    "right": "",
                }
            ]

        items: List[dict] = []
        for row in rows:
            due_display = self._format_due(row["due_date"], today)
            subtitle = row["subtitle"] or ""
            status = (row["status"] or "").lower()
            if status and status not in {"pending", "open", "todo"}:
                tag = status.upper()
                subtitle = f"{subtitle} [{tag}]".strip()
            items.append(
                {
                    "title": row["title"],
                    "subtitle": subtitle,
                    "right": due_display,
                }
            )
        return items

    @staticmethod
    def _format_due(value: str | None, today: date) -> str:
        if not value:
            return ""
        try:
            dt = datetime.fromisoformat(value)
        except Exception:  # noqa: BLE001
            return value[:10]
        due_date = dt.date()
        if due_date == today:
            return "HOJE"
        if due_date < today:
            delta = (today - due_date).days
            if delta == 1:
                return "Ontem"
            return f"-{delta}d"
        delta = (due_date - today).days
        if delta == 0:
            return "HOJE"
        if delta == 1:
            return "Amanhã"
        if delta <= 7:
            return f"{dt.strftime('%a')}"
        return dt.strftime("%d/%m")


__all__ = ["TaskDatabase"]
