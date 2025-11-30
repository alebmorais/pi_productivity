"""Utilities to persist task data for the e-paper display.

The Raspberry Pi setup does not have a database yet.  This module
creates a small SQLite database with a single ``tasks`` table and
provides helpers for synchronising Motion tasks and reading a compact
summary for the e-paper widget.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, List, Mapping, Sequence
from collections import defaultdict

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
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)"
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
            # Bug fix: Use a stable SHA1 hash of the JSON payload
            # to ensure the ID is deterministic.
            payload_bytes = json.dumps(payload, sort_keys=True).encode("utf-8")
            task_id = hashlib.sha1(payload_bytes).hexdigest()
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
    @staticmethod
    def _get_week_range(today: date) -> tuple[str, str]:
        """Return (start_of_week, end_of_week) as ISO strings for the current week.
        
        Week starts on Monday (weekday=0) and ends on Sunday (weekday=6).
        """
        # Calculate days since Monday
        days_since_monday = today.weekday()  # Monday=0, Sunday=6
        start_of_week = today - timedelta(days=days_since_monday)
        end_of_week = start_of_week + timedelta(days=6)
        
        return start_of_week.isoformat(), end_of_week.isoformat()

    def fetch_items_for_display(self, limit: int = 6) -> List[dict]:
        """Return a list of simplified entries for the e-paper display.
        
        Only shows tasks due within the current week (Monday to Sunday).
        """

        today = today_local()
        week_start, week_end = self._get_week_range(today)
        try:
            with self._connect() as conn:
                rows = conn.execute(
                    """
                    SELECT task_id, title, subtitle, due_date, status
                    FROM tasks
                    WHERE COALESCE(LOWER(status), 'pending') NOT IN ('completed', 'done', 'cancelled', 'canceled', 'archived')
                      AND due_date IS NOT NULL
                      AND DATE(due_date) >= ?
                      AND DATE(due_date) <= ?
                    ORDER BY
                        due_date ASC,
                        updated_at DESC
                    LIMIT ?
                    """,
                    (week_start, week_end, limit),
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
                    "title": "Sem tarefas esta semana",
                    "subtitle": "Aproveite para planejar ou descansar!",
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
                    "task_id": row["task_id"],
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

    def fetch_week_calendar(self, limit: int = 100) -> dict:
        """
        Return tasks grouped by day of the week for calendar view.

        The week always starts on Monday and ends on Sunday, matching the boundaries used by _get_week_range.

        The returned dictionary contains a list of days, each with its date, day name, day number, a flag indicating if it is today,
        and the list of tasks for that day. Tasks are grouped by day, and each day includes its name and number.

        If a database error occurs (e.g., sqlite3.Error), the returned dictionary will include an "error" field
        describing the exception.

        The maximum number of tasks returned for the week can be controlled via the 'limit' parameter.
        """
        today = today_local()
        week_start, week_end = self._get_week_range(today)
        
        try:
            with self._connect() as conn:
                rows = conn.execute(
                """
                SELECT task_id, title, subtitle, due_date, status, raw
                FROM tasks
                WHERE COALESCE(LOWER(status), 'pending') NOT IN ('completed', 'done', 'cancelled', 'canceled', 'archived')
                  AND due_date IS NOT NULL
                  AND DATE(due_date) >= ?
                  AND DATE(due_date) <= ?
                ORDER BY due_date ASC, updated_at DESC
                LIMIT ?
                """,
                (week_start, week_end, limit),
                ).fetchall()
        except sqlite3.Error as exc:
            return {
                "week_start": week_start,
                "week_end": week_end,
                "days": [],
                "error": str(exc)
            }
        
        tasks_by_date = defaultdict(list)
        for row in rows:
            due_date = row["due_date"][:10]
            tasks_by_date[due_date].append({
                "task_id": row["task_id"],
                "title": row["title"],
                "subtitle": row["subtitle"] or "",
                "status": row["status"] or "pending"
            })
        
        start_date = date.fromisoformat(week_start)
        day_names = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        days = []
        for i in range(7):
            current_date = start_date + timedelta(days=i)
            date_str = current_date.isoformat()
            
            days.append({
                "date": date_str,
                "day_name": day_names[i],
                "day_number": current_date.day,
                "is_today": current_date == today,
                "tasks": tasks_by_date.get(date_str, [])
            })
        
        return {
            "week_start": week_start,
            "week_end": week_end,
            "days": days
        }


__all__ = ["TaskDatabase"]
