mport os, requests, time
from typing import List, Dict, Any
from utils import today_local, parse_iso_date

BASE = os.getenv("MOTION_BASE_URL","https://api.usemotion.com/v1")
API_KEY = os.getenv("MOTION_API_KEY","wxhFEZLbpMk4a1m0lp0vZ1ZmNSfD0XLT2ItD/Mwnke8=")

class MotionClient:
    def __init__(self):
        if not API_KEY:
            raise RuntimeError("Defina MOTION_API_KEY no arquivo .env")
        self.sess = requests.Session()
        self.sess.headers.update({"X-API-Key": API_KEY})
        self.cache = {"tasks": [], "ts": 0}

    def get(self, path, params=None):
        r = self.sess.get(f"{BASE}{path}", params=params or {}, timeout=15)
        r.raise_for_status()
        return r.json()

    def list_tasks(self, force=False) -> List[Dict[str, Any]]:
        now = time.time()
        if not force and (now - self.cache["ts"]) < 60:
            return self.cache["tasks"]
        data = self.get("/tasks")   # GET sem ?limit
        tasks = data.get("tasks", data)
        self.cache = {"tasks": tasks, "ts": now}
        return tasks

    def build_today_queue(self, tasks: List[Dict[str, Any]]):
        today = today_local()
        groups = {"overdue": [], "due_today": [], "in_progress": [], "scheduled_today": []}

        def _to_str(x):
            if x is None:
                return ""
            if isinstance(x, dict):
                for k in ("name","status","state","value","type"):
                    v = x.get(k)
                    if isinstance(v,str):
                        return v
                return ""
            if isinstance(x,(list,tuple)):
                return " ".join([_to_str(i) for i in x])
            return str(x)

        def _labels_list(x):
            out=[]
            if not x: return out
            if isinstance(x,(list,tuple)):
                for item in x:
                    if isinstance(item,str):
                        out.append(item)
                    elif isinstance(item,dict):
                        for k in ("name","label","tag","value"):
                            v=item.get(k)
                            if isinstance(v,str):
                                out.append(v); break
            elif isinstance(x,dict):
                items=x.get("items")
                if isinstance(items,list):
                    out.extend(_labels_list(items))
        def _extract_date(v):
            if not v: return None
            if isinstance(v,str):
                return parse_iso_date(v)
            if isinstance(v,dict):
                for k in ("dueDate","due","date","start","end","startDate","scheduledStart"):
                    val=v.get(k)
                    if isinstance(val,str):
                        d=parse_iso_date(val)
                        if d: return d
            return None

        def is_overdue(t):
            d=_extract_date(t.get("dueDate"))
            return d is not None and d<today and (t.get("percentComplete",0)<100)

        def is_due_today(t):
            d=_extract_date(t.get("dueDate"))
            return d==today

        def is_in_progress(t):
            s=_to_str(t.get("status")).lower()
            pc=t.get("percentComplete", t.get("percent",0))
            try: pc=float(pc)
            except Exception: pc=0.0
            return ("progress" in s or "active" in s or "doing" in s) or (0<pc<100)

        def is_scheduled_today(t):
            d=_extract_date(t.get("startDate") or t.get("scheduledStart"))
            return d==today

        def has_today_label(t):
            labels=_labels_list(t.get("labels") or t.get("tags") or t.get("label"))
            labels=[_to_str(l).lower() for l in labels]
            return any(tag in labels for tag in ("today","#today","focus","#focus"))

        filtered=[t for t in tasks if (t.get("type") or "task").lower()=="task"]

        for t in filtered:
            if is_overdue(t): groups["overdue"].append(t); continue
            if is_due_today(t): groups["due_today"].append(t); continue
            if is_in_progress(t): groups["in_progress"].append(t); continue
            if is_scheduled_today(t) or has_today_label(t): groups["scheduled_today"].append(t); continue

        def sort_key(t):
            return (t.get("priority",999), t.get("dueDate") or t.get("startDate") or "9999-12-31")

        for k in groups:
            groups[k].sort(key=sort_key)

        queue=groups["overdue"]+groups["due_today"]+groups["in_progress"]+groups["scheduled_today"]
        compact=[]
        for t in queue:
            title=((t.get("name") or t.get("title") or t.get("summary") or "(sem título)"))[:22]
            due=_extract_date(t.get("dueDate"))
            right="HOJE" if (due and due==today) else (f"Venc: {due.strftime('%d/%m')}" if due else "")
            subtitle=""
            desc=(t.get("description") or "")
            for line in desc.splitlines():
                if line.strip().lower().startswith("next:"):
                    subtitle=line.split(":",1)[1].strip(); break
                if not subtitle: subtitle=_to_str(t.get("project") or t.get("projectId") or t.get("status") or "")
            compact.append({"id":t.get("id"),"title":title,"right":right,"subtitle":(subtitle or "")[:22]})
        return compact[:8]
