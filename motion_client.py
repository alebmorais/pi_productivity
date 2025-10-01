# motion_client.py
import os, requests
from dotenv import load_dotenv

load_dotenv(os.path.expanduser("~/pi_productivity/.env"))
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

    # ====== Funções utilitárias ======

    def list_all_tasks_simple(self, limit=200):
        data = self.get("/tasks", params={"limit": limit})
        return data.get("tasks", data)

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
        if labels: payload["labels"] = labels  # lista de strings
        if duration_minutes: payload["duration"] = int(duration_minutes)
        return self.post("/tasks", payload)

    def complete_task(self, task_id):
        return self.patch(f"/tasks/{task_id}", {"completed": True})
