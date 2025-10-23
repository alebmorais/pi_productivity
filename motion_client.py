import os, requests
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(os.path.expanduser("~/pi_productivity"))
dotenv_path = BASE_DIR / ".env"

# Load .env.example as a fallback if .env doesn't exist
if not dotenv_path.exists():
    dotenv_path = BASE_DIR / ".env.example"
    if dotenv_path.exists():
        print(f"Warning: .env file not found. Falling back to {dotenv_path}")

load_dotenv(dotenv_path=dotenv_path)

BASE = "https://api.usemotion.com/v1"

class MotionClient:
    def __init__(self):
        self.api_key = os.getenv("MOTION_API_KEY", "").strip()
        self.workspace_id = os.getenv("MOTION_WORKSPACE_ID", "").strip() # <--- ADICIONE ESTA LINHA
        self.sess = requests.Session()
        if self.api_key:
            self.sess.headers.update({
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json",
            })
        else:
            print("Warning: MOTION_API_KEY not set. Motion client will be non-functional.")

    def get(self, path, params=None):
        if not self.api_key:
            raise RuntimeError("MOTION_API_KEY is not configured.")
        r = self.sess.get(f"{BASE}{path}", params=params or {}, timeout=15)
        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            # Log detailed error info for debugging
            print(f"[Motion API Error] {e}")
            print(f"[Motion API Error] Response body: {r.text}")
            raise
        return r.json()

    def post(self, path, payload):
        if not self.api_key:
            raise RuntimeError("MOTION_API_KEY is not configured.")
        r = self.sess.post(f"{BASE}{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()

    def patch(self, path, payload):
        if not self.api_key:
            raise RuntimeError("MOTION_API_KEY is not configured.")
        r = self.sess.patch(f"{BASE}{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()

    def _extract_task_page(self, data):
        """Return ``(tasks, next_cursor, cursor_param)`` from *data*."""

        tasks_payload = data
        if isinstance(data, dict) and "tasks" in data:
            tasks_payload = data["tasks"]

        tasks_list = []
        if isinstance(tasks_payload, list):
            tasks_list = tasks_payload
        elif isinstance(tasks_payload, dict):
            for key in ("items", "data", "results", "entries", "records"):
                value = tasks_payload.get(key)
                if isinstance(value, list):
                    tasks_list = value
                    break
            else:
                # Some endpoints return the list directly under an unexpected key.
                flattened = [v for v in tasks_payload.values() if isinstance(v, list)]
                if flattened:
                    tasks_list = flattened[0]

        next_cursor = None
        cursor_param = None
        cursor_sources = []
        if isinstance(tasks_payload, dict):
            cursor_sources.append(tasks_payload)
        if isinstance(data, dict):
            cursor_sources.append(data)
        for source in cursor_sources:
            for key, param in (
                ("nextCursor", "cursor"),
                ("cursor", "cursor"),
                ("nextPageToken", "pageToken"),
                ("pageToken", "pageToken"),
                ("next", "cursor"),
            ):
                value = source.get(key)
                if value:
                    next_cursor = value
                    cursor_param = param
                    break
            if next_cursor:
                break

        return tasks_list, next_cursor, cursor_param

    def list_all_tasks_simple(self, limit=200):
        if not self.api_key:
            return []
        tasks = []
        cursor = None
        cursor_param = None

        while True:
            params = {}
            # Note: Motion API v1 does not accept 'limit' or 'workspaceId' as query params.
            # The API returns all tasks for the authenticated workspace automatically.
            # Pagination is handled via cursor if the API provides one.
            
            if cursor and cursor_param:
                params[cursor_param] = cursor

            data = self.get("/tasks", params=params)
            page_tasks, next_cursor, next_cursor_param = self._extract_task_page(data)
            if not isinstance(page_tasks, list):
                page_tasks = []
            tasks.extend(page_tasks)

            # If we have a limit and we've exceeded it, stop fetching more pages
            if limit is not None and len(tasks) >= limit:
                break

            if not next_cursor:
                break

            cursor = next_cursor
            cursor_param = next_cursor_param

        # Trim to the requested limit
        if limit is not None and len(tasks) > limit:
            tasks = tasks[:limit]

        return tasks

    def find_task_by_name(self, needle):
        if not needle: return None
        nl = needle.lower()
        for t in self.list_all_tasks_simple():
            name = (t.get("name") or t.get("title") or "")
            if nl in name.lower():
                return t
        return None

    def create_task(self, name, description="", due_date_iso=None, labels=None, duration_minutes=None):
        payload = {"name": name}
        if description: payload["description"] = description
        if due_date_iso: payload["dueDate"] = due_date_iso
        if labels: payload["labels"] = labels
        if duration_minutes: payload["duration"] = int(duration_minutes)
        return self.post("/tasks", payload)

    def complete_task(self, task_id):
        return self.patch(f"/tasks/{task_id}", {"completed": True})
