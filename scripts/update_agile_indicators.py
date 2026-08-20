import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from kanboard_mcp_server import kanboard_call

tasks_to_update = {
    51: {"priority": 1, "score": 35, "p_label": "P1 (Top Priority)", "c_label": "C35 (Considerable effort)"},
    53: {"priority": 1, "score": 25, "p_label": "P1 (Top Priority)", "c_label": "C25 (Effort required)"},
}
for t_id, data in tasks_to_update.items():
    task = kanboard_call("getTask", {"task_id": t_id})
    new_desc = f"**AgileIndicators:** Öncelik: `{data['p_label']}` | Karmaşıklık: `{data['c_label']}`\n\n" + task.get("description", "")
    kanboard_call("updateTask", {"id": t_id, "priority": data["priority"], "score": data["score"], "description": new_desc})
print("AgileIndicators updated.")
