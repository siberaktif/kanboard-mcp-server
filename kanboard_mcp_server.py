#!/usr/bin/env python3
"""
Kanboard MCP Sunucusu
Kanboard JSON-RPC API'sini MCP araçları olarak sunar.
"""

import json
import requests
import asyncio

from mcp.server.mcpserver import MCPServer

# ================== KANBOARD YAPILANDIRMASI ==================
KANBOARD_URL = "https://dedikanban.dedimetri.com/jsonrpc.php"
API_TOKEN = "12312db434d582512d6ba7180cefee218506095fb86cf49ad897776b05fd"   # <-- Kanboard API token'ını buraya koy
USERNAME = "jsonrpc"                            # Kanboard API kullanıcı adı sabittir

# ================== GÜVENLİK / ERİŞİM KONTROLÜ ==================
# İzin verilen proje ID'leri listesi. Yalnızca bu projelere erişime izin verilir.
# Not: Kanboard API zaten e-posta/kullanıcı bazlı yetkilendirmeye sahiptir. 
# Bu liste ek bir filtreleme (sadece seçili projeler) sağlar.
ALLOWED_PROJECT_IDS = [1, 3, 5]

def is_project_allowed(project_id) -> bool:
    if project_id is None:
        return False
    return int(project_id) in ALLOWED_PROJECT_IDS

# ================== KANBOARD API ÇAĞRISI ==================
def kanboard_call(method: str, params: dict | None = None):
    """
    Kanboard JSON-RPC API'sine istek gönderir ve 'result' kısmını döndürür.
    """
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1,
        "params": params or {}
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(
        KANBOARD_URL,
        json=payload,
        auth=(USERNAME, API_TOKEN),
        headers=headers,
        timeout=30
    )
    response.raise_for_status()  # HTTP hatası varsa fırlat
    data = response.json()
    if "error" in data:
        raise Exception(f"Kanboard API hatası: {data['error']}")
    return data.get("result")

# ================== MCP SUNUCUSU ==================
mcp = MCPServer("kanboard-mcp-server")

@mcp.tool()
def get_my_projects() -> str:
    """Kanboard'daki kendi projelerini listeler. Sadece ALLOWED_PROJECT_IDS içindeki izinli projeleri döndürür."""
    projects = kanboard_call("getMyProjects")
    if projects:
        # Filtreleme işlemi
        projects = [p for p in projects if is_project_allowed(p.get("id"))]
    return json.dumps(projects, indent=2, ensure_ascii=False)

@mcp.tool()
def get_project_by_id(project_id: int) -> str:
    """Tek bir projenin detayını getirir. Yalnızca ALLOWED_PROJECT_IDS listesinde varsa çalışır."""
    if not is_project_allowed(project_id):
        return json.dumps({"error": f"Proje ID {project_id} erişimine izin verilmiyor. İzin verilen projeler: {ALLOWED_PROJECT_IDS}"}, ensure_ascii=False)
    
    project = kanboard_call("getProjectById", {"project_id": project_id})
    return json.dumps(project, indent=2, ensure_ascii=False)

@mcp.tool()
def get_tasks_by_project(project_id: int) -> str:
    """Verilen proje ID'sindeki tüm görevleri getirir."""
    if not is_project_allowed(project_id):
        return json.dumps({"error": f"Proje ID {project_id} erişimine izin verilmiyor."}, ensure_ascii=False)

    tasks = kanboard_call("getAllTasks", {"project_id": project_id})
    return json.dumps(tasks, indent=2, ensure_ascii=False)

@mcp.tool()
def get_task_details(task_id: int) -> str:
    """Belirli bir görevin tüm detaylarını getirir (başlık, açıklama, atanan, kategori, tarih vb.)."""
    task = kanboard_call("getTask", {"task_id": task_id})
    if task and not is_project_allowed(task.get("project_id")):
        return json.dumps({"error": f"Bu görevin projesine erişim izniniz yok."}, ensure_ascii=False)

    return json.dumps(task, indent=2, ensure_ascii=False)

@mcp.tool()
def get_user_tasks() -> str:
    """Şu anki API kullanıcısının gecikmiş görevlerini getirir. Sadece izin verilen projelere ait olanları döndürür."""
    tasks = kanboard_call("getOverdueTasks")
    if tasks:
        tasks = [t for t in tasks if is_project_allowed(t.get("project_id"))]
    return json.dumps(tasks, indent=2, ensure_ascii=False)

@mcp.tool()
def get_columns(project_id: int) -> str:
    """Bir projedeki pano sütunlarını listeler. Taşıma veya görev oluşturma işlemleri için ID'leri bulmayı sağlar."""
    if not is_project_allowed(project_id):
        return json.dumps({"error": f"Proje ID {project_id} erişimine izin verilmiyor."}, ensure_ascii=False)
    
    columns = kanboard_call("getColumns", {"project_id": project_id})
    return json.dumps(columns, indent=2, ensure_ascii=False)

@mcp.tool()
def get_all_users() -> str:
    """Kanboard üzerindeki tüm kullanıcıları listeler (Görev atamalarında user_id'leri bulmak için kullanılır)."""
    users = kanboard_call("getAllUsers")
    return json.dumps(users, indent=2, ensure_ascii=False)

@mcp.tool()
def create_task(project_id: int, title: str, description: str = "", column_id: int = 0, owner_id: int = 0) -> str:
    """
    Yeni görev oluşturur.
    Zorunlu parametreler: project_id, title.
    İsteğe bağlı: description, column_id (0 ise varsayılan), owner_id (0 ise kimseye atanmaz).
    """
    if not is_project_allowed(project_id):
        return json.dumps({"error": f"Proje ID {project_id} erişimine izin verilmiyor."}, ensure_ascii=False)
    
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
        
    task_id = kanboard_call("createTask", params)
    return json.dumps({"message": "Görev oluşturuldu", "task_id": task_id}, ensure_ascii=False)

@mcp.tool()
def update_task(task_id: int, title: str = "", description: str = "", owner_id: int = 0, category_id: int = 0, score: int = 0) -> str:
    """
    Mevcut bir görevi günceller.
    En az bir alan sağlanmalıdır (title, description, owner_id, category_id, score vb.).
    """
    task = kanboard_call("getTask", {"task_id": task_id})
    if not task:
        return json.dumps({"error": "Görev bulunamadı."}, ensure_ascii=False)
    if not is_project_allowed(task.get("project_id")):
        return json.dumps({"error": "Bu görevin projesine erişim izniniz yok."}, ensure_ascii=False)

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
        
    if len(params) == 1:
        return json.dumps({"error": "Güncellenecek en az bir alan sağlamalısınız."}, ensure_ascii=False)

    result = kanboard_call("updateTask", params)
    return json.dumps({"message": "Görev güncellendi" if result else "Görev güncellenemedi", "result": result}, ensure_ascii=False)

@mcp.tool()
def move_task_position(project_id: int, task_id: int, column_id: int, position: int = 1) -> str:
    """
    Bir görevi belirli bir sütuna ve pozisyona taşır.
    """
    if not is_project_allowed(project_id):
        return json.dumps({"error": f"Proje ID {project_id} erişimine izin verilmiyor."}, ensure_ascii=False)
    
    params = {
        "project_id": project_id,
        "task_id": task_id,
        "column_id": column_id,
        "position": position
    }
    result = kanboard_call("moveTaskPosition", params)
    return json.dumps({"message": "Görev taşındı" if result else "Görev taşınamadı", "result": result}, ensure_ascii=False)

@mcp.tool()
def create_comment(task_id: int, user_id: int, content: str) -> str:
    """
    Belirli bir göreve yorum ekler. 
    user_id: Yorumu yapan kullanıcının ID'si.
    """
    task = kanboard_call("getTask", {"task_id": task_id})
    if not task:
        return json.dumps({"error": "Görev bulunamadı."}, ensure_ascii=False)
    if not is_project_allowed(task.get("project_id")):
        return json.dumps({"error": "Bu görevin projesine erişim izniniz yok."}, ensure_ascii=False)

    params = {
        "task_id": task_id,
        "user_id": user_id,
        "content": content
    }
    comment_id = kanboard_call("createComment", params)
    return json.dumps({"message": "Yorum eklendi", "comment_id": comment_id}, ensure_ascii=False)

async def main():
    await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())
