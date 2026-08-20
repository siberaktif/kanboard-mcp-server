import sys
import os
from collections import defaultdict
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from kanboard_mcp_server import kanboard_call

tasks = kanboard_call("getAllTasks", {"project_id": 2, "status_id": 1})
groups = defaultdict(list)
for task in tasks:
    groups[(int(task['swimlane_id']), int(task['column_id']))].append({'id': int(task['id']), 'title': task['title']})

for (sid, cid), task_list in groups.items():
    task_list.sort(key=lambda x: x['id'])
    for position, task in enumerate(task_list, start=1):
        kanboard_call("moveTaskPosition", {"project_id": 2, "task_id": task['id'], "column_id": cid, "position": position, "swimlane_id": sid})
print("Tasks reordered by ID.")
