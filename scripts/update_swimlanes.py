import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from kanboard_mcp_server import kanboard_call

kanboard_call("updateSwimlane", {"swimlane_id": 9, "project_id": 2, "name": "Bilgiler Kulvarı"})
swimlane_order = [9, 13, 14, 15, 10, 11, 12, 16, 17]
for position, swimlane_id in enumerate(swimlane_order, start=1):
    kanboard_call("changeSwimlanePosition", {"project_id": 2, "swimlane_id": swimlane_id, "position": position})
print("Swimlanes reordered successfully.")
