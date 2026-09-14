import argparse, json, base64, urllib.request, os, time, subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv("/home/sencarto/dediaiproje/dedisoft/kanboard-api-python/.env")

KB_URL = os.environ.get("KANBOARD_URL")
USERNAME = os.environ.get("KANBOARD_USERNAME")
API_TOKEN = os.environ.get("KANBOARD_USER_API_TOKEN")

def rpc_call(method, **kwargs):
    payload = {"jsonrpc": "2.0", "method": method, "id": 1, "params": kwargs}
    auth_str = f"{USERNAME}:{API_TOKEN}"
    base64_str = base64.b64encode(auth_str.encode("ascii")).decode("ascii")
    headers = {"Authorization": f"Basic {base64_str}", "Content-Type": "application/json"}
    req = urllib.request.Request(KB_URL, json.dumps(payload).encode('utf-8'), headers)
    try:
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            if 'error' in res:
                print(f"Error {method}: {res['error']}")
                return None
            return res.get('result')
    except Exception as e:
        print(f"Exception {method}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", type=int, required=True)
    parser.add_argument("--repo-path", type=str, required=True)
    parser.add_argument("--memory-dir", type=str, required=False)
    args = parser.parse_args()

    project_id = args.project_id

    # 1. Fetch existing tasks and map references
    print("Mapping existing tasks by reference for Upsert logic...")
    existing_tasks = {}
    for status in [1, 0]:
        tasks = rpc_call("getAllTasks", project_id=project_id, status_id=status)
        if tasks:
            for t in tasks:
                if t.get('reference'):
                    existing_tasks[t['reference']] = t['id']

    def upsert_task(ref, **kwargs):
        if ref in existing_tasks:
            task_id = existing_tasks[ref]
            # Sadece güncelle (dosyaları veya bağlantıları silmemek için)
            rpc_call("updateTask", id=task_id, title=kwargs['title'], description=kwargs['description'], color_id=kwargs['color_id'], score=kwargs['score'], priority=kwargs['priority'], date_started=kwargs['date_started'], date_due=kwargs['date_due'])
            return task_id, False
        else:
            task_id = rpc_call("createTask", reference=ref, **kwargs)
            return task_id, True

    prev_task_id = 0
    count_new = 0
    count_updated = 0

    # Phase 0 Tasks
    if args.memory_dir and os.path.isdir(args.memory_dir):
        print("Processing Phase 0 (AI Memory) tasks...")
        
        # Phase 0.1
        t1_start = datetime(2026, 8, 28, 10, 0)
        t1_end = datetime(2026, 8, 30, 18, 0)
        t1_ref = "phase0:gemini"
        
        t1_id, t1_is_new = upsert_task(
            t1_ref,
            project_id=project_id,
            title="Görev 00.1: Konsept, İhtiyaç Analizi ve Fizibilite (Gemini İstişaresi)",
            description="Çoklu proje verilerinin tekilleştirilmesi, Glassmorphism yönetici paneli hedefleri.",
            color_id="purple", score=10, priority=3,
            date_started=t1_start.strftime("%Y-%m-%d %H:%M"),
            date_due=t1_end.strftime("%Y-%m-%d %H:%M"),
            creator_id=1, owner_id=1
        )
        if t1_id:
            if t1_is_new:
                count_new += 1
                f1_path = os.path.join(args.memory_dir, "gemini_fizibilite_raporu.md")
                if os.path.isfile(f1_path):
                    with open(f1_path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode('ascii')
                    rpc_call("createTaskFile", project_id=project_id, task_id=t1_id, filename="gemini_fizibilite_raporu.md", blob=b64)
                rpc_call("closeTask", task_id=t1_id)
            else:
                count_updated += 1
            prev_task_id = t1_id

        # Phase 0.2
        t2_start = datetime(2026, 8, 31, 9, 0)
        t2_end = datetime(2026, 8, 31, 18, 0)
        t2_ref = "phase0:deepseek"
        
        t2_id, t2_is_new = upsert_task(
            t2_ref,
            project_id=project_id,
            title="Görev 00.2: Eklenti Mimarisi ve Dizin İzolasyonu (DeepSeek Kod İncelemesi)",
            description="Kanboard hook mekanizması, Controller-Template ayrımı, SQL kancalarının tespiti.",
            color_id="purple", score=10, priority=3,
            date_started=t2_start.strftime("%Y-%m-%d %H:%M"),
            date_due=t2_end.strftime("%Y-%m-%d %H:%M"),
            creator_id=1, owner_id=1
        )
        if t2_id:
            if t2_is_new:
                count_new += 1
                f2_path = os.path.join(args.memory_dir, "deepseek_mimari_kararlar.md")
                if os.path.isfile(f2_path):
                    with open(f2_path, "rb") as f:
                        b64 = base64.b64encode(f.read()).decode('ascii')
                    rpc_call("createTaskFile", project_id=project_id, task_id=t2_id, filename="deepseek_mimari_kararlar.md", blob=b64)
                if prev_task_id > 0:
                    rpc_call("createTaskLink", task_id=prev_task_id, opposite_task_id=t2_id, link_id=2)
                rpc_call("closeTask", task_id=t2_id)
            else:
                count_updated += 1
            prev_task_id = t2_id

    print("Reading git log...")
    git_cmd = ['git', '-C', args.repo_path, 'log', '--reverse', '--pretty=format:COMMIT:%h|%at|%s%nBODY:%b%n---']
    try:
        raw_log = subprocess.check_output(git_cmd, text=True)
    except Exception as e:
        print(f"Git log failed: {e}")
        return

    commits = [c for c in raw_log.split("---") if c.strip()]
    step_num = 1

    for commit in commits:
        lines = commit.strip().split('\n')
        commit_line = lines[0]
        if not commit_line.startswith("COMMIT:"): continue
        
        parts = commit_line.replace("COMMIT:", "").split("|")
        commit_hash = parts[0]
        commit_epoch = int(parts[1])
        commit_msg = parts[2]
        body = "\n".join(lines[1:]).replace("BODY:", "").strip()
        
        color = "green"
        priority = 1
        score = 3
        
        msg_low = commit_msg.lower()
        if "fix:" in msg_low or "kriz" in msg_low or "bug" in msg_low:
            color = "red"
            priority = 3
            score = 8
        elif "feat:" in msg_low or "refactor:" in msg_low:
            color = "blue"
            priority = 2
            score = 5
            
        commit_time = datetime.fromtimestamp(commit_epoch)
        date_started_str = commit_time.strftime("%Y-%m-%d %H:%M")
        date_due_str = (commit_time + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M")
        
        desc_md = f"**Otantik Forgejo Tarihçesi**\n\n{body}\n\n* Commit: {commit_hash}\n* Unix Timestamp: {commit_epoch}"
        ref = f"commit:{commit_hash}"
        
        task_id, is_new = upsert_task(
            ref,
            project_id=project_id,
            title=f"Adım {step_num}: {commit_msg}",
            description=desc_md,
            color_id=color,
            score=score,
            priority=priority,
            date_started=date_started_str,
            date_due=date_due_str,
            creator_id=1, owner_id=1
        )
        
        if task_id:
            if is_new:
                count_new += 1
                rpc_call("createSubtask", task_id=task_id, title="Değişiklikler incelendi ve test edildi.", status=2, time_estimated=2, time_spent=2, user_id=1)
                rpc_call("createExternalTaskLink", task_id=task_id, url=f"http://localhost:3010/sencarto/ExecutiveDashboard-plugin-kanboard/commit/{commit_hash}", dependency="related", type="weblink", title=f"Forgejo: {commit_hash}")
                rpc_call("createExternalTaskLink", task_id=task_id, url=f"https://github.com/siberaktif/ExecutiveDashboard-plugin-kanboard/commit/{commit_hash}", dependency="related", type="weblink", title=f"GitHub: {commit_hash}")
                if prev_task_id > 0:
                    rpc_call("createTaskLink", task_id=prev_task_id, opposite_task_id=task_id, link_id=2)
                rpc_call("closeTask", task_id=task_id)
                print(f"Created task {task_id} for {commit_hash}")
            else:
                count_updated += 1
                # print(f"Updated task {task_id} for {commit_hash}")
            
            prev_task_id = task_id
            
        step_num += 1

    print(f"DONE! Tasks Created: {count_new}, Tasks Updated: {count_updated}")

if __name__ == "__main__":
    main()
