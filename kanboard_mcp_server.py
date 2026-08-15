#!/usr/bin/env python3
"""
Kanboard MCP Sunucusu
Kanboard JSON-RPC API'sini MCP araçları olarak sunar.
.env dosyasından yapılandırma ayarlarını yükler.
"""

import os
import json
import requests
import asyncio
from dotenv import load_dotenv

from mcp.server.mcpserver import MCPServer

# ================== YAPILANDIRMA ==================
# Çevresel değişkenleri yükle (.env dosyasından)
load_dotenv()

KANBOARD_URL = os.getenv("KANBOARD_URL", "https://dedikanban.dedimetri.com/jsonrpc.php")
KANBOARD_USERNAME = os.getenv("KANBOARD_USERNAME", "jsonrpc")
KANBOARD_PASSWORD = os.getenv("KANBOARD_PASSWORD", "")
KANBOARD_API_TOKEN = os.getenv("KANBOARD_API_TOKEN", "")

# Kanboard HTTP Basic Auth için doğrulama bilgilerini belirle
# API Token önceliklidir (Kişisel Token veya Sistem Tokenı)
if KANBOARD_API_TOKEN:
    # Eğer username varsayılan 'jsonrpc' ise sistem tokenı gibi davranır. 
    # Özel bir kullanıcı adı verilmişse, kullanıcının kişisel token'ı olarak işlem görür.
    AUTH = (KANBOARD_USERNAME, KANBOARD_API_TOKEN)
else:
    # E-posta / Parola tabanlı yetkilendirme
    AUTH = (KANBOARD_USERNAME, KANBOARD_PASSWORD)

# ================== KANBOARD API ÇAĞRISI ==================
def kanboard_call(method: str, params: dict | None = None):
    """
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
        response.raise_for_status()  # HTTP hatası varsa fırlat
        data = response.json()
        
        if "error" in data:
            error_data = data["error"]
            error_msg = str(error_data)
            
            # Kanboard genelde yetkisiz erişimlerde Access Denied hatası döndürür.
            if isinstance(error_data, dict) and error_data.get("message") == "Access Denied":
                raise PermissionError("Bu projeye veya veriye erişim yetkiniz yok.")
            else:
                raise Exception(f"Kanboard API hatası: {error_msg}")
                
        return data.get("result")
        
    except requests.exceptions.RequestException as e:
        raise Exception(f"Bağlantı hatası: {str(e)}")


def safe_execute(func, *args, **kwargs) -> str:
    """API çağrısını çalıştırıp olası hataları (yetki vs.) düzgün bir JSON'a sararak döndürür."""
    try:
        result = func(*args, **kwargs)
        return json.dumps(result, indent=2, ensure_ascii=False)
    except PermissionError as pe:
        return json.dumps({"error": str(pe)}, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


# ================== MCP SUNUCUSU ==================
mcp = MCPServer("kanboard-mcp-server")

@mcp.tool()
def get_my_projects() -> str:
    """
    Kanboard'daki kendi projelerini listeler. 
    Kullanıcıya özel yetkili (ve atanmış olunan) projeleri döndürür.
    """
    return safe_execute(kanboard_call, "getMyProjects")

@mcp.tool()
def get_project_by_id(project_id: int) -> str:
    """Tek bir projenin detayını getirir. Yetkiniz olmayan projede hata döndürür."""
    return safe_execute(kanboard_call, "getProjectById", {"project_id": project_id})

@mcp.tool()
def get_tasks_by_project(project_id: int) -> str:
    """Verilen proje ID'sindeki tüm görevleri getirir."""
    return safe_execute(kanboard_call, "getAllTasks", {"project_id": project_id})

@mcp.tool()
def get_task_details(task_id: int) -> str:
    """Belirli bir görevin tüm detaylarını getirir (başlık, açıklama, atanan, kategori, tarih vb.)."""
    return safe_execute(kanboard_call, "getTask", {"task_id": task_id})

@mcp.tool()
def get_user_tasks() -> str:
    """Şu anki API kullanıcısının (veya token sahibinin) gecikmiş ve açık görevlerini getirir."""
    return safe_execute(kanboard_call, "getOverdueTasks")

@mcp.tool()
def get_columns(project_id: int) -> str:
    """Bir projedeki pano sütunlarını listeler. Taşıma veya görev oluşturma işlemleri için ID'leri bulmayı sağlar."""
    return safe_execute(kanboard_call, "getColumns", {"project_id": project_id})

# =========================================================================
# GÜVENLİK NOTU: Tüm kullanıcıları listelemek, mevcut kullanıcının sadece 
# yetkili olduğu projeler dışında sistemdeki herkesi görmesine yol açabilir. 
# Bu sebeple bu araç varsayılan olarak devre dışı (yorum satırı) bırakılmıştır.
#
# @mcp.tool()
# def get_all_users() -> str:
#     """Kanboard üzerindeki tüm kullanıcıları listeler (Görev atamalarında user_id'leri bulmak için kullanılır)."""
#     return safe_execute(kanboard_call, "getAllUsers")
# =========================================================================

@mcp.tool()
def create_task(project_id: int, title: str, description: str = "", column_id: int = 0, owner_id: int = 0) -> str:
    """
    Yeni görev oluşturur. Sadece yetkili olduğunuz projelere görev oluşturabilirsiniz.
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
        return {"message": "Görev oluşturuldu", "task_id": task_id}
        
    return safe_execute(_execute)

@mcp.tool()
def update_task(task_id: int, title: str = "", description: str = "", owner_id: int = 0, category_id: int = 0, score: int = 0) -> str:
    """
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
        return json.dumps({"error": "Güncellenecek en az bir alan sağlamalısınız."}, ensure_ascii=False)

    def _execute():
        result = kanboard_call("updateTask", params)
        return {"message": "Görev güncellendi" if result else "Görev güncellenemedi", "result": result}
        
    return safe_execute(_execute)

@mcp.tool()
def move_task_position(project_id: int, task_id: int, column_id: int, position: int = 1) -> str:
    """
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
        return {"message": "Görev taşındı" if result else "Görev taşınamadı", "result": result}
        
    return safe_execute(_execute)

@mcp.tool()
def create_comment(task_id: int, user_id: int, content: str) -> str:
    """
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
        return {"message": "Yorum eklendi", "comment_id": comment_id}
        
    return safe_execute(_execute)


async def main():
    await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())
