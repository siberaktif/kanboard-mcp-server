import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from kanboard_mcp_server import kanboard_call

tasks = [
    (51, 13), (52, 13), (53, 13), (54, 10),
    (55, 10), (56, 15), (57, 17), (58, 16)
]
for t_id, s_id in tasks:
    kanboard_call("moveTaskPosition", {
        "project_id": 2, "task_id": t_id, "column_id": 10, "position": 1, "swimlane_id": s_id
    })
    print(f"Task {t_id} moved to swimlane {s_id}")
