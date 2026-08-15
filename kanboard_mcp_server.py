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
    """Kanboard'daki kendi projelerini listeler. Proje ID, isim ve açıklama döndürür."""
    projects = kanboard_call("getMyProjects")
    return json.dumps(projects, indent=2, ensure_ascii=False)

@mcp.tool()
def get_tasks_by_project(project_id: int) -> str:
    """Verilen proje ID'sindeki tüm görevleri getirir. Görevler; başlık, durum, atanan kişi gibi bilgileri içerir."""
    tasks = kanboard_call("getAllTasks", {"project_id": project_id})
    return json.dumps(tasks, indent=2, ensure_ascii=False)

@mcp.tool()
def get_task_details(task_id: int) -> str:
    """Belirli bir görevin tüm detaylarını getirir (başlık, açıklama, atanan, kategori, tarih vb.)."""
    task = kanboard_call("getTask", {"task_id": task_id})
    return json.dumps(task, indent=2, ensure_ascii=False)

@mcp.tool()
def get_user_tasks() -> str:
    """Şu anki API kullanıcısının gecikmiş görevlerini getirir."""
    tasks = kanboard_call("getOverdueTasks")
    return json.dumps(tasks, indent=2, ensure_ascii=False)

async def main():
    await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())
