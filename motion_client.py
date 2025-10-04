import os, requests
from dotenv import load_dotenv

BASE_DIR = os.path.expanduser("~/pi_productivity")
load_dotenv(os.path.join(BASE_DIR, ".env"))

BASE = "https://api.usemotion.com/v1"

class MotionClient:
    def __init__(self):
        api = os.getenv("MOTION_API_KEY","").strip()
        if not api:
            raise RuntimeError("Defina MOTION_API_KEY no arquivo .env")
        self.sess = requests.Session()
        self.sess.headers.update({"X-API-Key": api})

    def get(self, path, params=None):
        r = self.sess.get(f"{BASE}{path}", params=params or {}, timeout=15)
        r.raise_for_status()
        return r.json()

    def post(self, path, payload):
        r = self.sess.post(f"{BASE}{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()

    def patch(self, path, payload):
        r = self.sess.patch(f"{BASE}{path}", json=payload, timeout=15)
        r.raise_for_status()
        return r.json()

    def list_all_tasks_simple(self, limit=200):
        max_limit = 100  # Motion caps the page size at 100 items.
        tasks = []
        remaining = None if limit is None else max(0, int(limit))
        cursor = None
        cursor_param = None

        while True:
            params = {}
            if remaining is None:
                params["limit"] = max_limit
            elif remaining == 0:
                break
            else:
                params["limit"] = min(remaining, max_limit)

            if cursor and cursor_param:
                params[cursor_param] = cursor

            data = self.get("/tasks", params=params)
            page_tasks = data.get("tasks", data)
            if not isinstance(page_tasks, list):
                page_tasks = []
            tasks.extend(page_tasks)

            if remaining is not None:
                remaining = max(0, remaining - len(page_tasks))
                if remaining == 0:
                    break

            next_cursor = None
            next_cursor_param = None
            if "nextCursor" in data and data["nextCursor"]:
                next_cursor = data["nextCursor"]
                next_cursor_param = "cursor"
            elif "nextPageToken" in data and data["nextPageToken"]:
                next_cursor = data["nextPageToken"]
                next_cursor_param = "pageToken"
            elif "cursor" in data and data["cursor"]:
                next_cursor = data["cursor"]
                next_cursor_param = "cursor"

            if not next_cursor:
                break

            cursor = next_cursor
            cursor_param = next_cursor_param

        if remaining is not None and len(tasks) > limit:
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
