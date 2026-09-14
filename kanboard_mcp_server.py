#!/usr/bin/env python3
"""
Kanboard MCP Server
Exposes Kanboard JSON-RPC API as MCP tools.
Loads configuration settings from the .env file.

Kanboard MCP Sunucusu
Kanboard JSON-RPC API'sini MCP araçları olarak sunar.
.env dosyasından yapılandırma ayarlarını yükler.
"""

import os
import sys
import json
import argparse
import requests
import asyncio
from dotenv import load_dotenv

from mcp.server.mcpserver import MCPServer

# ================== CONFIGURATION / YAPILANDIRMA ==================
# Load environment variables (from .env file)
# Çevresel değişkenleri yükle (.env dosyasından)
load_dotenv()

KANBOARD_URL = os.getenv("KANBOARD_URL", "https://your-kanboard-server.com/jsonrpc.php")

# User Credentials (Kullanıcı Bilgileri)
KANBOARD_USERNAME = os.getenv("KANBOARD_USERNAME", "")
KANBOARD_USERMAIL = os.getenv("KANBOARD_USERMAIL", "")
KANBOARD_PASSWORD = os.getenv("KANBOARD_PASSWORD", "")
KANBOARD_USER_API_TOKEN = os.getenv("KANBOARD_USER_API_TOKEN", "")

# App Credentials (Genel Sistem Bilgileri)
KANBOARD_APP_USERNAME = os.getenv("KANBOARD_APP_USERNAME", "jsonrpc")
KANBOARD_APP_API_TOKEN = os.getenv("KANBOARD_APP_API_TOKEN", "")

# Determine credentials for Kanboard HTTP Basic Auth
# Kullanıcı adı belirleme: KANBOARD_USERNAME öncelikli, boşsa KANBOARD_USERMAIL kullanılır.
user_login = KANBOARD_USERNAME if KANBOARD_USERNAME else KANBOARD_USERMAIL

# Auth Priority / Bağlantı Önceliği:
# 1. User API Token (Personal) -> auth=(user_login, KANBOARD_USER_API_TOKEN)
# 2. App API Token (Global) -> auth=(KANBOARD_APP_USERNAME, KANBOARD_APP_API_TOKEN)
# 3. Password -> auth=(user_login, KANBOARD_PASSWORD)

if user_login and KANBOARD_USER_API_TOKEN:
    AUTH = (user_login, KANBOARD_USER_API_TOKEN)
    auth_mode = "User API Token"
elif KANBOARD_APP_API_TOKEN:
    AUTH = (KANBOARD_APP_USERNAME, KANBOARD_APP_API_TOKEN)
    auth_mode = "App API Token (Warning: 'My' methods like getMyProjects will fail)"
elif user_login and KANBOARD_PASSWORD:
    AUTH = (user_login, KANBOARD_PASSWORD)
    auth_mode = "User Password"
else:
    AUTH = (KANBOARD_APP_USERNAME, '')
    auth_mode = "None"

# ================== KANBOARD API CALL / KANBOARD API ÇAĞRISI ==================
def kanboard_call(method: str, params: dict | None = None):
    """
    Sends a request to Kanboard JSON-RPC API and returns the 'result' part.
    Raises Exception in case of unauthorized access.
    
    Kanboard JSON-RPC API'sine istek gönderir ve 'result' kısmını döndürür.
    Yetkisiz erişim durumunda Exception fırlatır.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1,
        "params": params or {}
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(
            KANBOARD_URL,
            json=payload,
            auth=AUTH,
            headers=headers,
            timeout=30
        )
        response.raise_for_status()  # Raise HTTP errors if any / HTTP hatası varsa fırlat
        data = response.json()
        
        if "error" in data:
            error_data = data["error"]
            error_msg = str(error_data)
            
            # Kanboard generally returns an Access Denied error for unauthorized access.
            # Kanboard genelde yetkisiz erişimlerde Access Denied hatası döndürür.
            if isinstance(error_data, dict) and error_data.get("message") == "Access Denied":
                raise PermissionError("You do not have permission to access this project or data. / Bu projeye veya veriye erişim yetkiniz yok.")
            else:
                raise Exception(f"Kanboard API error / Kanboard API hatası: {error_msg}")
                
        return data.get("result")
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Connection error / Bağlantı hatası: {str(e)}")


def safe_execute(func, *args, **kwargs) -> str:
    """
    Executes the API call and wraps possible errors (auth, etc.) into a proper JSON response.
    
    API çağrısını çalıştırıp olası hataları (yetki vs.) düzgün bir JSON'a sararak döndürür.
    """
    try:
        result = func(*args, **kwargs)
        return json.dumps(result, indent=2, ensure_ascii=False)
    except PermissionError as pe:
        return json.dumps({"error": str(pe)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# ================== MCP SERVER / MCP SUNUCUSU ==================
mcp = MCPServer("kanboard-mcp-server")

@mcp.tool()
def get_my_projects() -> str:
    """
    Lists your own projects in Kanboard. 
    Kanboard API automatically returns only the projects the user (email/user) is authorized for.

    Kanboard'daki kendi projelerini listeler. 
    Kanboard API'si otomatik olarak sadece kullanıcının e-posta/kullanıcı ile yetkili olduğu projeleri döndürür.
    """
    return safe_execute(kanboard_call, "getMyProjects")

@mcp.tool()
def get_project_by_id(project_id: int) -> str:
    """
    Gets the details of a single project. Returns an error for unauthorized projects.
    
    Tek bir projenin detayını getirir. Yetkiniz olmayan projede hata döndürür.
    """
    return safe_execute(kanboard_call, "getProjectById", {"project_id": project_id})

@mcp.tool()
def get_tasks_by_project(project_id: int) -> str:
    """
    Gets all tasks in the given project ID.
    
    Verilen proje ID'sindeki tüm görevleri getirir.
    """
    return safe_execute(kanboard_call, "getAllTasks", {"project_id": project_id})

@mcp.tool()
def get_task_details(task_id: int) -> str:
    """
    Gets all details of a specific task (title, description, assignee, category, date, etc.).
    
    Belirli bir görevin tüm detaylarını getirir (başlık, açıklama, atanan, kategori, tarih vb.).
    """
    return safe_execute(kanboard_call, "getTask", {"task_id": task_id})

@mcp.tool()
def get_user_tasks() -> str:
    """
    Gets the overdue and open tasks of the current API user (or token owner).
    
    Şu anki API kullanıcısının (veya token sahibinin) gecikmiş ve açık görevlerini getirir.
    """
    return safe_execute(kanboard_call, "getOverdueTasks")

@mcp.tool()
def get_columns(project_id: int) -> str:
    """
    Lists the board columns in a project. Used to find IDs for moving tasks or creating tasks.
    
    Bir projedeki pano sütunlarını listeler. Taşıma veya görev oluşturma işlemleri için ID'leri bulmayı sağlar.
    """
    return safe_execute(kanboard_call, "getColumns", {"project_id": project_id})

# =========================================================================
# SECURITY NOTE: Listing all users might allow the current user to see 
# everyone in the system outside of their authorized projects. 
# Therefore, this tool is disabled (commented out) by default.
#
# GÜVENLİK NOTU: Tüm kullanıcıları listelemek, mevcut kullanıcının sadece 
# yetkili olduğu projeler dışında sistemdeki herkesi görmesine yol açabilir. 
# Bu sebeple bu araç varsayılan olarak devre dışı (yorum satırı) bırakılmıştır.
#
# @mcp.tool()
# def get_all_users() -> str:
#     """
#     Lists all users on Kanboard (used to find user_ids for task assignments).
#     Kanboard üzerindeki tüm kullanıcıları listeler (Görev atamalarında user_id'leri bulmak için kullanılır).
#     """
#     return safe_execute(kanboard_call, "getAllUsers")
# =========================================================================

@mcp.tool()
def create_task(project_id: int, title: str, description: str = "", column_id: int = 0, owner_id: int = 0, swimlane_id: int = 0) -> str:
    """
    Creates a new task. You can only create tasks in projects you are authorized for.
    Required parameters: project_id, title.
    Optional: description, column_id (0 for default), owner_id (0 to assign to nobody).

    Yeni görev oluşturur. Sadece yetkili olduğunuz projelere görev oluşturabilirsiniz.
    Zorunlu parametreler: project_id, title.
    İsteğe bağlı: description, column_id (0 ise varsayılan), owner_id (0 ise kimseye atanmaz).
    """
    params = {
        "project_id": project_id,
        "title": title,
    }
    if description:
        params["description"] = description
    if column_id > 0:
        params["column_id"] = column_id
    if owner_id > 0:
        params["owner_id"] = owner_id
    if swimlane_id > 0:
        params["swimlane_id"] = swimlane_id
        
    def _execute():
        task_id = kanboard_call("createTask", params)
        return {"message": "Task created / Görev oluşturuldu", "task_id": task_id}
        
    return safe_execute(_execute)

@mcp.tool()
def update_task(task_id: int, title: str = "", description: str = "", owner_id: int = 0, category_id: int = 0, score: int = 0, swimlane_id: int = 0) -> str:
    """
    Updates an existing task.
    At least one field must be provided (title, description, owner_id, category_id, score, etc.).

    Mevcut bir görevi günceller.
    En az bir alan sağlanmalıdır (title, description, owner_id, category_id, score vb.).
    """
    params = {"id": task_id}
    if title:
        params["title"] = title
    if description:
        params["description"] = description
    if owner_id > 0:
        params["owner_id"] = owner_id
    if category_id > 0:
        params["category_id"] = category_id
    if score > 0:
        params["score"] = score
    if swimlane_id > 0:
        params["swimlane_id"] = swimlane_id
        
    if len(params) == 1:
        return json.dumps({"error": "You must provide at least one field to update. / Güncellenecek en az bir alan sağlamalısınız."}, ensure_ascii=False)

    def _execute():
        result = kanboard_call("updateTask", params)
        return {"message": "Task updated / Görev güncellendi" if result else "Task could not be updated / Görev güncellenemedi", "result": result}
        
    return safe_execute(_execute)

@mcp.tool()
def move_task_position(project_id: int, task_id: int, column_id: int, position: int = 1, swimlane_id: int = 0) -> str:
    """
    Moves a task to a specific column and position.

    Bir görevi belirli bir sütuna ve pozisyona taşır.
    """
    params = {
        "project_id": project_id,
        "task_id": task_id,
        "column_id": column_id,
        "position": position
    }
    if swimlane_id > 0:
        params["swimlane_id"] = swimlane_id
    def _execute():
        result = kanboard_call("moveTaskPosition", params)
        return {"message": "Task moved / Görev taşındı" if result else "Task could not be moved / Görev taşınamadı", "result": result}
        
    return safe_execute(_execute)

@mcp.tool()
def create_comment(task_id: int, user_id: int, content: str) -> str:
    """
    Adds a comment to a specific task.
    user_id: The ID of the user making the comment.

    Belirli bir göreve yorum ekler. 
    user_id: Yorumu yapan kullanıcının ID'si.
    """
    params = {
        "task_id": task_id,
        "user_id": user_id,
        "content": content
    }
    def _execute():
        comment_id = kanboard_call("createComment", params)
        return {"message": "Comment added / Yorum eklendi", "comment_id": comment_id}
        
    return safe_execute(_execute)


@mcp.tool()
def get_all_subtasks(task_id: int) -> str:
    """
    Gets all subtasks for a given task.
    Belirli bir görevin tüm alt görevlerini getirir.
    """
    return safe_execute(kanboard_call, "getAllSubtasks", {"task_id": task_id})

@mcp.tool()
def create_subtask(task_id: int, title: str, time_estimated: int = 0) -> str:
    """
    Creates a single subtask.
    Tek bir alt görev oluşturur.
    """
    params = {"task_id": task_id, "title": title}
    if time_estimated > 0:
        params["time_estimated"] = time_estimated
    def _execute():
        res = kanboard_call("createSubtask", params)
        return {"message": "Subtask created / Alt görev oluşturuldu", "subtask_id": res}
    return safe_execute(_execute)

@mcp.tool()
def create_bulk_subtasks(task_id: int, titles_csv: str) -> str:
    """
    Creates multiple subtasks from a comma-separated string of titles.
    Virgülle ayrılmış başlıklardan çoklu alt görev oluşturur.
    Example: titles_csv="Subtask 1, Subtask 2"
    """
    titles = [t.strip() for t in titles_csv.split(",") if t.strip()]
    def _execute():
        ids = []
        for title in titles:
            ids.append(kanboard_call("createSubtask", {"task_id": task_id, "title": title}))
        return {"message": f"{len(ids)} subtasks created / alt görev oluşturuldu", "ids": ids}
    return safe_execute(_execute)

@mcp.tool()
def get_all_swimlanes(project_id: int) -> str:
    """
    Lists all swimlanes for a project.
    Bir projeye ait tüm kulvarları (swimlanes) listeler.
    """
    return safe_execute(kanboard_call, "getAllSwimlanes", {"project_id": project_id})

@mcp.tool()
def change_swimlane_position(project_id: int, swimlane_id: int, position: int) -> str:
    """
    Changes the position of a swimlane.
    Bir kulvarın (swimlane) sırasını (pozisyonunu) değiştirir.
    """
    params = {"project_id": project_id, "swimlane_id": swimlane_id, "position": position}
    def _execute():
        res = kanboard_call("changeSwimlanePosition", params)
        return {"message": "Swimlane position changed / Kulvar sırası değişti" if res else "Failed / Başarısız"}
    return safe_execute(_execute)

@mcp.tool()
def create_milestone(project_id: int, title: str, column_id: int, date_str: str) -> str:
    """
    Creates a milestone task (colored yellow) for a specific date.
    Belirtilen tarih için sarı renkli bir kilometre taşı (milestone) görevi oluşturur.
    date_str format: YYYY-MM-DD
    """
    params = {
        "project_id": project_id,
        "title": f"🚩 KİLOMETRE TAŞI: {title}",
        "column_id": column_id,
        "date_started": date_str,
        "date_due": date_str,
        "color_id": "yellow"
    }
    def _execute():
        res = kanboard_call("createTask", params)
        return {"message": "Milestone created / Kilometre taşı oluşturuldu", "task_id": res}
    return safe_execute(_execute)

@mcp.tool()
def schedule_waterfall(task_ids_csv: str, start_date_str: str, hours_per_subtask: int = 4) -> str:
    """
    Schedules a list of tasks sequentially (waterfall) starting from start_date_str.
    Updates time_estimated based on subtasks.
    Bir görev listesini ardışık (şelale) olarak planlar. Alt görev sayısına göre tahmini süreyi hesaplar.
    task_ids_csv: "748,749,750"
    start_date_str: "2026-08-20"
    """
    import datetime
    
    try:
        task_ids = [int(x.strip()) for x in task_ids_csv.split(",") if x.strip().isdigit()]
        current_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    except Exception as e:
        return json.dumps({"error": f"Invalid format / Geçersiz format: {str(e)}"}, ensure_ascii=False)
        
    def _execute():
        nonlocal current_date
        results = []
        for t_id in task_ids:
            subtasks = kanboard_call("getAllSubtasks", {"task_id": t_id})
            num_subtasks = len(subtasks) if subtasks else 1
            total_hours = num_subtasks * hours_per_subtask
            days_needed = num_subtasks
            
            start_fmt = current_date.strftime("%Y-%m-%d")
            end_date = current_date + datetime.timedelta(days=max(days_needed - 1, 0))
            end_fmt = end_date.strftime("%Y-%m-%d")
            
            if subtasks:
                for st in subtasks:
                    kanboard_call("updateSubtask", {"id": st["id"], "task_id": t_id, "time_estimated": hours_per_subtask})
                    
            kanboard_call("updateTask", {"id": t_id, "date_started": start_fmt, "date_due": end_fmt, "time_estimated": total_hours})
            
            results.append({"task_id": t_id, "start": start_fmt, "end": end_fmt, "total_hours": total_hours})
            current_date = end_date + datetime.timedelta(days=1)
            
        return {"message": "Waterfall scheduling completed / Şelale planlama tamamlandı", "schedule": results}
    return safe_execute(_execute)

@mcp.tool()
def get_project_master_map(project_id: int) -> str:
    """
    Aggregates project metadata, active tasks, and project files into a single context map for Agent Swarm.

    Context Aggregator for Kanboard — fetches project metadata, active tasks, and
    documentation files in one call to provide full project context to agents.

    Kanboard icin Baglam Toplayici — proje meta verilerini, aktif gorevleri ve
    dokumantasyon dosyalarini tek cagrida birlestirerek ajanlara tam proje baglami saglar.

    Args:
        project_id (int): Kanboard project ID / Kanboard proje IDsi.

    Returns:
        JSON string with keys: project, active_tasks, project_files, markdown_docs, summary
        (and optional errors for partial failures). Returns structured error JSON if
        project_id is invalid or project not found.
    """
    if isinstance(project_id, bool) or not isinstance(project_id, int):
        return json.dumps({"error": f"Invalid project_id type: expected int, got {type(project_id).__name__}"}, ensure_ascii=False)
    if project_id <= 0:
        return json.dumps({"error": f"Invalid project_id: must be positive integer, got {project_id}"}, ensure_ascii=False)

    errors: list[str] = []
    project_data: dict | None = None
    active_tasks: list[dict] = []
    project_files: list[dict] = []
    markdown_docs: list[dict] = []
    column_map: dict[str, str] = {}

    # a) Fetch project metadata via getProjectById
    try:
        raw_project = kanboard_call("getProjectById", {"project_id": project_id})
        if not raw_project:
            return json.dumps({"error": f"Project {project_id} not found"}, ensure_ascii=False)
        pid_val = raw_project.get("id", project_id)
        try:
            pid_int = int(pid_val)
        except Exception:
            pid_int = project_id
        is_active_raw = raw_project.get("is_active", raw_project.get("isActive", "1"))
        if isinstance(is_active_raw, str):
            is_active = is_active_raw == "1"
        elif isinstance(is_active_raw, bool):
            is_active = is_active_raw
        else:
            try:
                is_active = int(is_active_raw) == 1
            except Exception:
                is_active = bool(is_active_raw)
        project_data = {
            "id": pid_int,
            "name": raw_project.get("name", ""),
            "is_active": is_active,
            "description": raw_project.get("description", ""),
        }
    except PermissionError as pe:
        return json.dumps({"error": str(pe)}, ensure_ascii=False)
    except Exception as e:
        msg = str(e)
        if "not found" in msg.lower() or "Access Denied" in msg:
            return json.dumps({"error": f"Project {project_id} not found: {msg}"}, ensure_ascii=False)
        return json.dumps({"error": f"Failed to fetch project {project_id}: {msg}"}, ensure_ascii=False)

    # b) Fetch all tasks via getAllTasks, filter is_active == 1 (handles "1"/"0" strings)
    try:
        raw_tasks = kanboard_call("getAllTasks", {"project_id": project_id})
        if raw_tasks is None:
            raw_tasks = []
        if not isinstance(raw_tasks, list):
            errors.append(f"getAllTasks returned unexpected type: {type(raw_tasks).__name__}")
            raw_tasks = []
        try:
            raw_columns = kanboard_call("getColumns", {"project_id": project_id})
            if isinstance(raw_columns, list):
                for col in raw_columns:
                    cid = str(col.get("id", ""))
                    title = col.get("title", col.get("name", ""))
                    if cid:
                        column_map[cid] = title
        except Exception as ce:
            errors.append(f"getColumns failed: {str(ce)}")
        for t in raw_tasks:
            is_active_val = t.get("is_active", "1")
            try:
                active_flag = str(is_active_val) == "1" or int(is_active_val) == 1
            except Exception:
                active_flag = bool(is_active_val)
            if not active_flag:
                continue
            try:
                tid = int(t.get("id", 0))
            except Exception:
                continue
            col_name = t.get("column_name") or t.get("column_title") or ""
            if not col_name:
                cid = str(t.get("column_id", ""))
                col_name = column_map.get(cid, cid)
            assignee = (
                t.get("assignee_name")
                or t.get("assignee_username")
                or t.get("assignee")
                or t.get("owner_name")
                or t.get("owner_username")
                or t.get("username")
                or t.get("user_name")
            )
            if not assignee:
                oid = t.get("owner_id", t.get("ownerId", 0))
                assignee = oid if oid not in (None, "") else 0
                try:
                    assignee = int(assignee)
                except Exception:
                    pass
                if assignee == 0 or assignee == "0":
                    assignee = None
            active_tasks.append({
                "id": tid,
                "title": t.get("title", ""),
                "column_name": col_name,
                "assignee": assignee,
            })
    except PermissionError as pe:
        errors.append(f"getAllTasks permission error: {str(pe)}")
    except Exception as e:
        errors.append(f"getAllTasks failed: {str(e)}")

    # c) Fetch attachments via getAllProjectFiles (fallback to getProjectFiles)
    try:
        raw_files = None
        last_file_error = None
        for method_name in ["getAllProjectFiles", "getProjectFiles"]:
            try:
                raw_files = kanboard_call(method_name, {"project_id": project_id})
                if isinstance(raw_files, list):
                    break
                if raw_files is None:
                    raw_files = []
                    break
            except Exception as fe:
                last_file_error = str(fe)
                if "Method not found" in last_file_error or "not found" in last_file_error.lower():
                    continue
                if "Access Denied" in last_file_error or "permission" in last_file_error.lower():
                    raise
                continue
        if raw_files is None:
            if last_file_error:
                errors.append(f"getAllProjectFiles failed: {last_file_error}")
            raw_files = []
        if not isinstance(raw_files, list):
            errors.append(f"getAllProjectFiles returned unexpected type: {type(raw_files).__name__}")
            raw_files = []
        for f in raw_files:
            fid_raw = f.get("id", f.get("file_id", f.get("fileId", 0)))
            try:
                fid = int(fid_raw)
            except Exception:
                fid = fid_raw
            fname = f.get("name", f.get("filename", f.get("original_filename", f.get("file_name", ""))))
            is_md = isinstance(fname, str) and fname.lower().endswith(".md")
            entry: dict = {"id": fid, "name": fname, "is_markdown": is_md}
            if "size" in f:
                entry["size"] = f["size"]
            if "date" in f:
                entry["date"] = f["date"]
            project_files.append(entry)
        markdown_docs = [pf for pf in project_files if pf.get("is_markdown")]
    except PermissionError as pe:
        errors.append(f"getAllProjectFiles permission error: {str(pe)}")
    except Exception as e:
        errors.append(f"getAllProjectFiles failed: {str(e)}")

    result: dict = {
        "project": project_data,
        "active_tasks": active_tasks,
        "project_files": project_files,
        "markdown_docs": markdown_docs,
        "summary": {
            "active_task_count": len(active_tasks),
            "total_files": len(project_files),
            "markdown_count": len(markdown_docs),
        },
    }
    if errors:
        result["errors"] = errors
    return json.dumps(result, indent=2, ensure_ascii=False)

# ================== CLI COMMANDS / KOMUT SATIRI ==================
async def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--help', action='store_true', help="Show help message / Yardım mesajını gösterir")
    parser.add_argument('--status', action='store_true', help="Show server status / Sunucu durumunu gösterir")
    parser.add_argument('--doctor', action='store_true', help="Run diagnostics / Teşhis aracını çalıştırır")
    
    # We use parse_known_args in case MCP passes other internal args.
    args, unknown = parser.parse_known_args()

    if args.help:
        print("Kanboard MCP Server CLI")
        print("-" * 30)
        print("--help   : Show this help message / Bu yardım mesajını gösterir")
        print("--status : Show server status / Sunucu durumunu gösterir")
        print("--doctor : Run diagnostics (.env check, network & auth test) / Teşhis araçlarını çalıştırır (.env kontrolü, bağlantı testi)")
        sys.exit(0)
        
    if args.status:
        print("Status / Durum: Kanboard MCP Server is configured and ready. / Kanboard MCP Sunucusu yapılandırıldı ve hazır.")
        sys.exit(0)
        
    if args.doctor:
        print("Running diagnostics... / Teşhis çalıştırılıyor...\n")
        
        print("[.env Validation / .env Doğrulaması]")
        print(f"- KANBOARD_URL exists / mevcut: {'Yes (Evet)' if KANBOARD_URL else 'No (Hayır)'}")
        print(f"- KANBOARD_USERNAME exists / mevcut: {'Yes (Evet)' if KANBOARD_USERNAME else 'No (Hayır)'}")
        print(f"- KANBOARD_USERMAIL exists / mevcut: {'Yes (Evet)' if KANBOARD_USERMAIL else 'No (Hayır)'}")
        print(f"- KANBOARD_USER_API_TOKEN exists / mevcut: {'Yes (Evet)' if KANBOARD_USER_API_TOKEN else 'No (Hayır)'}")
        print(f"- KANBOARD_APP_USERNAME exists / mevcut: {'Yes (Evet)' if KANBOARD_APP_USERNAME else 'No (Hayır)'}")
        print(f"- KANBOARD_APP_API_TOKEN exists / mevcut: {'Yes (Evet)' if KANBOARD_APP_API_TOKEN else 'No (Hayır)'}")
        print(f"- KANBOARD_PASSWORD exists / mevcut: {'Yes (Evet)' if KANBOARD_PASSWORD else 'No (Hayır)'}")
        print("")
        
        print("[Network & Auth / Ağ ve Yetki Testi]")
        print(f"- Selected Auth Mode / Seçilen Bağlantı Modu: {auth_mode}")
        if auth_mode.startswith("App API Token"):
            print("  ! WARNING: Application API does not support user-specific methods like getMyProjects or getOverdueTasks.")
            print("  ! UYARI: Uygulama API'si (jsonrpc), kullanıcıya özel (getMyProjects, getOverdueTasks vb.) metodları desteklemez!")
        # Test basic internet
        try:
            requests.get("https://1.1.1.1", timeout=5)
            print("- Internet connection: OK / İnternet bağlantısı: Başarılı")
        except:
            print("- Internet connection: FAILED / İnternet bağlantısı: BAŞARISIZ")
            
        # Test Kanboard Connection
        try:
            print("- Testing Kanboard JSON-RPC connection... / Kanboard JSON-RPC bağlantısı test ediliyor...")
            kanboard_call("getVersion")
            print("=> Server connection & Auth: OK / Sunucu bağlantısı ve Yetki: Başarılı!")
        except Exception as e:
            print(f"=> Server connection & Auth: FAILED / Sunucu bağlantısı ve Yetki: BAŞARISIZ!")
            print(f"   Reason / Sebep: {str(e)}")
            
        sys.exit(0)

    # Standard MCP Run / Standart MCP Başlatma
    msg_en = "Starting Kanboard MCP Server... Press Ctrl+C to stop."
    msg_tr = "Kanboard MCP Sunucusu başlatılıyor... Durdurmak için Ctrl+C tuşlarına basın."
    # NOTE: Output must be written to stderr to not break MCP stdio protocol JSON parsing.
    # NOT: MCP stdio protokolünü (JSON) bozmamak için loglar stderr'e yazılmalıdır.
    print(f"{msg_en}\n{msg_tr}\n", file=sys.stderr)
    
    await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())

@mcp.tool()
def create_external_task_link(task_id: int, url: str, dependency: str, type: str = "weblink", title: str = "") -> str:
    """
    Creates an external link for a task.
    Required: task_id, url, dependency (e.g. "related").
    """
    try:
        res = kanboard_call("createExternalTaskLink", {
            "task_id": task_id,
            "url": url,
            "dependency": dependency,
            "type": type,
            "title": title
        })
        if res:
            return f"Success: External link created with ID {res}"
        return "Failed to create external link"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def create_task_link(task_id: int, opposite_task_id: int, link_id: int) -> str:
    """
    Creates a link between two tasks.
    link_id: 1 (relates to), 2 (blocks), 3 (is blocked by), etc.
    """
    try:
        res = kanboard_call("createTaskLink", {
            "task_id": task_id,
            "opposite_task_id": opposite_task_id,
            "link_id": link_id
        })
        if res:
            return f"Success: Task link created with ID {res}"
        return "Failed to create task link"
    except Exception as e:
        return f"Error: {str(e)}"

@mcp.tool()
def close_task(task_id: int) -> str:
    """
    Closes a task (sets is_active to 0).
    """
    try:
        res = kanboard_call("closeTask", {"task_id": task_id})
        if res:
            return f"Success: Task {task_id} closed"
        return f"Failed to close task {task_id}"
    except Exception as e:
        return f"Error: {str(e)}"
