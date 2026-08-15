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
def create_task(project_id: int, title: str, description: str = "", column_id: int = 0, owner_id: int = 0) -> str:
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
        
    def _execute():
        task_id = kanboard_call("createTask", params)
        return {"message": "Task created / Görev oluşturuldu", "task_id": task_id}
        
    return safe_execute(_execute)

@mcp.tool()
def update_task(task_id: int, title: str = "", description: str = "", owner_id: int = 0, category_id: int = 0, score: int = 0) -> str:
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
        
    if len(params) == 1:
        return json.dumps({"error": "You must provide at least one field to update. / Güncellenecek en az bir alan sağlamalısınız."}, ensure_ascii=False)

    def _execute():
        result = kanboard_call("updateTask", params)
        return {"message": "Task updated / Görev güncellendi" if result else "Task could not be updated / Görev güncellenemedi", "result": result}
        
    return safe_execute(_execute)

@mcp.tool()
def move_task_position(project_id: int, task_id: int, column_id: int, position: int = 1) -> str:
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
