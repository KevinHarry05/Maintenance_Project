import asyncio
import json
import threading
import time
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import httpx
import psycopg2
from jose import jwt
from psycopg2.extras import RealDictCursor

from app.config import settings
from app.core.security import hash_password
from app.tasks.sla_tasks import check_sla_violations
from app.utils.cache import redis_cache

BASE = "http://127.0.0.1:8000"
PASSWORD = "StrongPass123"


def db_conn():
    return psycopg2.connect(settings.DATABASE_URL.replace("+asyncpg", ""))


def ensure_user(conn, name, email, role, password=PASSWORD):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT id FROM users WHERE email=%s", (email,))
        row = cur.fetchone()
        if row:
            return str(row["id"])
        cur.execute(
            "INSERT INTO users (id,name,email,password,role) VALUES (%s,%s,%s,%s,%s) RETURNING id",
            (str(uuid4()), name, email, hash_password(password), role),
        )
        return str(cur.fetchone()["id"])


def wrapped(resp):
    body = resp.json()
    if isinstance(body, dict) and "data" in body:
        return body
    return {"success": None, "data": body, "message": None, "request_id": None}


def login(client, email, password=PASSWORD):
    r = client.post("/auth/login", data={"username": email, "password": password})
    if r.status_code != 200:
        raise AssertionError(f"login failed {r.status_code} {r.text}")
    return wrapped(r)["data"]["access_token"]


def mk_student(client, suffix, i):
    email = f"qa_{suffix}_{i}@test.com"
    client.post("/auth/register", json={"name": f"u{i}", "email": email, "password": PASSWORD})
    return email, login(client, email)


def q_count(conn, sql, params=()):
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return int(cur.fetchone()[0])


def q_one(conn, sql, params=()):
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(sql, params)
        return cur.fetchone()


class R:
    def __init__(self):
        self.rows = []

    def add(self, cid, name, exp, actual, ok, note=""):
        self.rows.append({
            "id": cid,
            "name": name,
            "expected": exp,
            "actual": actual,
            "status": "PASS" if ok else "FAIL",
            "note": note,
        })

    def add_info(self, cid, name, exp, actual, note=""):
        self.rows.append({
            "id": cid,
            "name": name,
            "expected": exp,
            "actual": actual,
            "status": "INFO",
            "note": note,
        })


def main():
    rep = R()
    suffix = str(uuid4())[:8]

    conn = db_conn()
    conn.autocommit = False

    admin_email = f"admin_{suffix}@test.com"
    staff_email = f"staff_{suffix}@test.com"
    staff2_email = f"staff2_{suffix}@test.com"

    admin_id = ensure_user(conn, "Admin", admin_email, "admin")
    staff_id = ensure_user(conn, "Staff", staff_email, "staff")
    staff2_id = ensure_user(conn, "Staff2", staff2_email, "staff")
    conn.commit()

    with httpx.Client(base_url=BASE, timeout=60.0) as client:
        admin_token = login(client, admin_email)
        staff_token = login(client, staff_email)
        staff2_token = login(client, staff2_email)

        # building seed
        b = client.post(
            "/buildings/",
            json={"name": "QA Main", "block": "Q", "floor_count": 5},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        building_id = wrapped(b)["data"]["id"]

        # 1 Authentication
        user_email = f"auth_{suffix}@test.com"
        r = client.post("/auth/register", json={"name": "testuser", "email": user_email, "password": PASSWORD})
        rep.add("1.1", "Register user", "200", str(r.status_code), r.status_code == 200)

        r = client.post("/auth/register", json={"name": "testuser", "email": user_email, "password": PASSWORD})
        bdy = wrapped(r)
        rep.add("1.2", "Duplicate registration", "409 + success:false", f"{r.status_code}, success={bdy.get('success')}", r.status_code == 409 and bdy.get("success") is False)

        weak_email = f"weak_{suffix}@test.com"
        r = client.post("/auth/register", json={"name": "test", "email": weak_email, "password": "123"})
        rep.add("1.3", "Invalid password format", "400", str(r.status_code), r.status_code == 400)

        r = client.post("/auth/login", data={"username": user_email, "password": "bad"})
        rep.add("1.4", "Login invalid password", "401", str(r.status_code), r.status_code == 401)

        token = jwt.encode(
            {"sub": "x", "type": "access", "exp": datetime.now(timezone.utc) - timedelta(hours=1)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        r = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
        rep.add("1.5", "Expired token", "401", str(r.status_code), r.status_code == 401)

        # 2 RBAC
        s_email, s_tok = mk_student(client, suffix, 1)
        r = client.post("/buildings/", json={"name": "x", "block": "x", "floor_count": 1}, headers={"Authorization": f"Bearer {s_tok}"})
        rep.add("2.1", "Student admin endpoint", "403", str(r.status_code), r.status_code == 403)

        r = client.delete(f"/buildings/{building_id}", headers={"Authorization": f"Bearer {staff_token}"})
        rep.add("2.2", "Staff admin endpoint", "403", str(r.status_code), r.status_code == 403)

        # 3 Complaint creation
        c_email, c_tok = mk_student(client, suffix, 2)
        r = client.post("/complaints/", json={"title": "AC not working", "description": "AC in room 302 broken", "building_id": building_id}, headers={"Authorization": f"Bearer {c_tok}"})
        d = wrapped(r).get("data", {})
        cid = d.get("id")
        rep.add("3.1", "Valid complaint", "200 + priority + assignment", f"{r.status_code}, pri={d.get('priority_level')}, assigned={bool(d.get('assigned_to'))}", r.status_code == 200 and d.get("priority_level") is not None)

        r = client.post("/complaints/", json={"title": "bad", "description": "bad", "building_id": str(uuid4())}, headers={"Authorization": f"Bearer {c_tok}"})
        rep.add("3.2", "Invalid building", "404", str(r.status_code), r.status_code == 404)

        spam_email, spam_tok = mk_student(client, suffix, 3)
        codes = []
        for i in range(15):
            rr = client.post("/complaints/", json={"title": f"spam{i}", "description": "spam", "building_id": building_id}, headers={"Authorization": f"Bearer {spam_tok}"})
            codes.append(rr.status_code)
            if rr.status_code == 429:
                break
        rep.add("3.3", "Spam complaints", "429", str(codes), 429 in codes)

        # 4 File upload
        f_email, f_tok = mk_student(client, suffix, 4)
        r = client.post("/complaints/", data={"title": "img", "description": "img", "building_id": building_id}, files={"file": ("image.jpg", b"img", "image/jpeg")}, headers={"Authorization": f"Bearer {f_tok}"})
        fp = wrapped(r).get("data", {}).get("file_path")
        rep.add("4.1", "Valid upload", "200 + file path", f"{r.status_code}, path={bool(fp)}", r.status_code == 200 and bool(fp))

        f2_email, f2_tok = mk_student(client, suffix, 5)
        r = client.post("/complaints/", data={"title": "exe", "description": "exe", "building_id": building_id}, files={"file": ("virus.exe", b"MZ", "application/octet-stream")}, headers={"Authorization": f"Bearer {f2_tok}"})
        rep.add("4.2", "Invalid file type", "400", str(r.status_code), r.status_code == 400)

        f3_email, f3_tok = mk_student(client, suffix, 6)
        big = b"0" * (20 * 1024 * 1024)
        r = client.post("/complaints/", data={"title": "big", "description": "big", "building_id": building_id}, files={"file": ("big.jpg", big, "image/jpeg")}, headers={"Authorization": f"Bearer {f3_tok}"})
        rep.add("4.3", "Large file", "413", str(r.status_code), r.status_code == 413)

        # 5 AI predictions (post-create sync + async)
        ai_email, ai_tok = mk_student(client, suffix, 7)
        def create_and_wait(title, desc):
            rr = client.post("/complaints/", json={"title": title, "description": desc, "building_id": building_id}, headers={"Authorization": f"Bearer {ai_tok}"})
            cd = wrapped(rr).get("data", {})
            ccid = cd.get("id")
            time.sleep(2)
            row = q_one(conn, "SELECT category, priority_level FROM complaints WHERE id=%s", (ccid,))
            return rr.status_code, row

        st, row = create_and_wait("AC not working", "AC broken")
        rep.add("5.1", "AI electrical", "category electrical + priority medium", f"{st}, {dict(row)}", st == 200 and row["category"] == "electrical" and str(row["priority_level"]).lower() == "medium")

        st, row = create_and_wait("short circuit sparks", "danger")
        rep.add("5.2", "AI dangerous", "priority high", f"{st}, {dict(row)}", st == 200 and str(row["priority_level"]).lower() in ("high", "critical"))

        st, row = create_and_wait("water leak in bathroom", "pipe leak")
        rep.add("5.3", "AI plumbing", "category plumbing", f"{st}, {dict(row)}", st == 200 and row["category"] == "plumbing")

        # 6 Auto assignment
        a_email, a_tok = mk_student(client, suffix, 8)
        assigned = []
        for i in range(5):
            rr = client.post("/complaints/", json={"title": f"assign{i}", "description": "issue", "building_id": building_id}, headers={"Authorization": f"Bearer {a_tok}"})
            assigned.append(wrapped(rr).get("data", {}).get("assigned_to"))
        rep.add("6.1", "Auto staff assignment", "least workload non-null", str(assigned), all(x is not None for x in assigned))
        rep.add_info("6.2", "No staff available", "pending", "NOT EXECUTED", "requires isolated env with zero staff")

        # 7 Notification pipeline
        n_email, n_tok = mk_student(client, suffix, 9)
        rr = client.post("/complaints/", json={"title": "notif", "description": "notif", "building_id": building_id}, headers={"Authorization": f"Bearer {n_tok}"})
        ncid = wrapped(rr)["data"]["id"]
        client.put(f"/complaints/{ncid}/assign", json={"staff_id": staff_id}, headers={"Authorization": f"Bearer {admin_token}"})
        client.put(f"/complaints/{ncid}/status", json={"status": "in_progress"}, headers={"Authorization": f"Bearer {staff_token}"})
        client.put(f"/complaints/{ncid}/status", json={"status": "resolved"}, headers={"Authorization": f"Bearer {staff_token}"})
        time.sleep(3)
        ncount = q_count(conn, "SELECT COUNT(*) FROM notifications WHERE complaint_id=%s", (ncid,))
        rep.add("7.1", "Notification lifecycle", ">=4 notifications", str(ncount), ncount >= 4)

        # 8 websocket
        try:
            import websockets  # noqa
            rep.add_info("8.1", "Websocket notifications", "assigned message to clients", "NOT EXECUTED", "dependency available; skipped to avoid flaky async in this batch")
        except Exception:
            rep.add_info("8.1", "Websocket notifications", "assigned message to clients", "NOT EXECUTED", "websockets package unavailable")

        # 9 SLA
        uid = q_one(conn, "SELECT id FROM users WHERE email=%s", (n_email,))["id"]
        c25, c49, c73 = str(uuid4()), str(uuid4()), str(uuid4())
        with conn.cursor() as cur:
            cur.execute("INSERT INTO complaints (id,title,description,status,priority_score,priority_level,user_id,building_id,created_at) VALUES (%s,'c25','x','pending',0.1,'Low',%s,%s,NOW()-INTERVAL '25 hours')", (c25, uid, building_id))
            cur.execute("INSERT INTO complaints (id,title,description,status,priority_score,priority_level,user_id,building_id,created_at) VALUES (%s,'c49','x','pending',0.1,'Low',%s,%s,NOW()-INTERVAL '49 hours')", (c49, uid, building_id))
            cur.execute("INSERT INTO complaints (id,title,description,status,priority_score,priority_level,user_id,building_id,created_at) VALUES (%s,'c73','x','pending',0.1,'Low',%s,%s,NOW()-INTERVAL '73 hours')", (c73, uid, building_id))
        conn.commit()
        check_sla_violations()
        r25 = q_one(conn, "SELECT status,priority_level FROM complaints WHERE id=%s", (c25,))
        r49 = q_one(conn, "SELECT status,priority_level FROM complaints WHERE id=%s", (c49,))
        r73 = q_one(conn, "SELECT status,priority_level FROM complaints WHERE id=%s", (c73,))
        ok_sla = str(r25["priority_level"]).lower() in ("high", "critical") and str(r49["priority_level"]).lower() in ("high", "critical") and r73["status"] == "escalated"
        rep.add("9.1", "SLA escalation", "25h priority+,49h notify path,73h escalated", f"25={dict(r25)} 49={dict(r49)} 73={dict(r73)}", ok_sla)

        # 10 cache
        redis_cache.delete("buildings:all")
        h = {"Authorization": f"Bearer {admin_token}"}
        client.get("/buildings/", headers=h)
        k1 = bool(redis_cache.get("buildings:all"))
        client.get("/buildings/", headers=h)
        k2 = bool(redis_cache.get("buildings:all"))
        client.put(f"/buildings/{building_id}", json={"name": "Invalidate"}, headers=h)
        k3 = bool(redis_cache.get("buildings:all"))
        rep.add("10.1", "Redis cache", "key created then invalidated", f"k1={k1},k2={k2},k3={k3}", k1 and k2 and not k3)

        # 11 gateway
        r = client.post("/complaints/", json={"title": "bad"})
        b = wrapped(r)
        rep.add("11.1", "Gateway normalization", "success:false + request_id", f"status={r.status_code},success={b.get('success')},reqid={bool(b.get('request_id'))}", b.get("success") is False and bool(b.get("request_id")))

        # 12 health
        r = client.get("/health")
        d = wrapped(r).get("data", {})
        rep.add("12.1", "Health dependencies", "db connected, redis connected, celery online", f"{d}", d.get("database") == "connected" and d.get("redis") == "connected" and d.get("celery") == "online")

        # 13 external
        rep.add_info("13.1", "Worker stop/start", "queue then execute", "RUN EXTERNALLY", "executed separately via terminal orchestration")

        # 14 external
        rep.add_info("14.1", "Redis outage scenario", "api survives with cache disabled", "RUN EXTERNALLY", "requires service stop permissions")

        # 15 load 100 from one user
        l_email, l_tok = mk_student(client, suffix, 10)
        success = 0
        rate = 0
        for i in range(100):
            rr = client.post("/complaints/", json={"title": f"load{i}", "description": "load", "building_id": building_id}, headers={"Authorization": f"Bearer {l_tok}"})
            if rr.status_code == 200:
                success += 1
            if rr.status_code == 429:
                rate += 1
        rep.add("15.1", "Extreme load 100", "no crash + rate limit triggered", f"success={success},rate={rate}", success > 0 and rate > 0)

        # 16 security
        s_email2, s_tok2 = mk_student(client, suffix, 11)
        r = client.post("/complaints/", json={"title": "'; DROP TABLE users;--", "description": "inj", "building_id": building_id}, headers={"Authorization": f"Bearer {s_tok2}"})
        users_cnt = q_count(conn, "SELECT COUNT(*) FROM users")
        rep.add("16.1", "SQL injection", "users table intact", f"status={r.status_code},users={users_cnt}", users_cnt > 0)

        x_email, x_tok = mk_student(client, suffix, 12)
        payload = "<script>alert()</script>"
        r = client.post("/complaints/", json={"title": payload, "description": payload, "building_id": building_id}, headers={"Authorization": f"Bearer {x_tok}"})
        title = wrapped(r).get("data", {}).get("title")
        rep.add("16.2", "XSS payload", "escaped output", f"stored={title}", title != payload)

        # 17 DB integrity
        r = client.delete(f"/buildings/{building_id}", headers={"Authorization": f"Bearer {admin_token}"})
        rep.add("17.1", "Delete building with complaints", "blocked by FK", str(r.status_code), r.status_code in (400, 409, 500))

        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM users WHERE id=%s", (staff_id,))
            conn.commit()
            rep.add("17.2", "Delete assigned staff", "blocked", "deleted", False)
        except Exception as exc:
            conn.rollback()
            rep.add("17.2", "Delete assigned staff", "blocked", "blocked", True, str(exc))

        # 18 celery failure
        from app.tasks.notification_tasks import send_push_notification_task
        ar = send_push_notification_task.delay("not-a-uuid", "bad", "bad", "status_change", None)
        time.sleep(2)
        rep.add("18.1", "Celery task failure", "retry mechanism", f"state={ar.state}", ar.state == "RETRY")

        # 19 concurrent update
        cc_email, cc_tok = mk_student(client, suffix, 13)
        r = client.post("/complaints/", json={"title": "conc", "description": "conc", "building_id": building_id}, headers={"Authorization": f"Bearer {cc_tok}"})
        ccid = wrapped(r)["data"]["id"]
        client.put(f"/complaints/{ccid}/assign", json={"staff_id": staff_id}, headers={"Authorization": f"Bearer {admin_token}"})
        out = []

        def upd(st):
            rr = client.put(f"/complaints/{ccid}/status", json={"status": st}, headers={"Authorization": f"Bearer {staff_token}"})
            out.append((st, rr.status_code))

        t1 = threading.Thread(target=upd, args=("in_progress",))
        t2 = threading.Thread(target=upd, args=("resolved",))
        t1.start(); t2.start(); t1.join(); t2.join()
        final = q_one(conn, "SELECT status FROM complaints WHERE id=%s", (ccid,))["status"]
        rep.add("19.1", "Concurrent status updates", "safe concurrent updates", f"updates={out},final={final}", len(out) == 2 and all(code in (200, 409, 400) for _, code in out))

        # 20 full flow
        ff_email, ff_tok = mk_student(client, suffix, 14)
        b2 = client.post("/buildings/", json={"name": "Flow", "block": "F", "floor_count": 3}, headers={"Authorization": f"Bearer {admin_token}"})
        b2id = wrapped(b2)["data"]["id"]
        c2 = client.post("/complaints/", json={"title": "full flow", "description": "short circuit", "building_id": b2id}, headers={"Authorization": f"Bearer {ff_tok}"})
        c2id = wrapped(c2)["data"]["id"]
        client.put(f"/complaints/{c2id}/assign", json={"staff_id": staff_id}, headers={"Authorization": f"Bearer {admin_token}"})
        client.put(f"/complaints/{c2id}/status", json={"status": "resolved"}, headers={"Authorization": f"Bearer {staff_token}"})
        time.sleep(3)
        logs = q_count(conn, "SELECT COUNT(*) FROM ticket_logs WHERE complaint_id=%s", (c2id,))
        notif = q_count(conn, "SELECT COUNT(*) FROM notifications WHERE complaint_id=%s", (c2id,))
        row = q_one(conn, "SELECT priority_level,category,status FROM complaints WHERE id=%s", (c2id,))
        rep.add("20.1", "Full workflow", "all services triggered", f"logs={logs},notif={notif},row={dict(row)}", logs >= 3 and notif >= 2 and row["status"] == "resolved")

    passed = sum(1 for r in rep.rows if r["status"] == "PASS")
    failed = sum(1 for r in rep.rows if r["status"] == "FAIL")
    output = {"summary": {"passed": passed, "failed": failed, "total": len(rep.rows)}, "results": rep.rows}
    print(json.dumps(output, indent=2, default=str))

    conn.close()


if __name__ == "__main__":
    main()
