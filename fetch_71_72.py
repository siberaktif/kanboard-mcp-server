import os
import json
import requests
from dotenv import load_dotenv

# Load env from kanboard-api-python
load_dotenv('/home/sencarto/dediaiproje/dedisoft/kanboard-api-python/.env')

url = os.getenv("KANBOARD_URL")
user = os.getenv("KANBOARD_APP_USERNAME") or os.getenv("KANBOARD_USERNAME")
token = os.getenv("KANBOARD_APP_API_TOKEN") or os.getenv("KANBOARD_USER_API_TOKEN")

def rpc_call(method, params=None):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1,
        "params": params or {}
    }
    response = requests.post(url, auth=(user, token), json=payload)
    response.raise_for_status()
    res = response.json()
    if 'error' in res:
        print(f"Error in {method}: {res['error']}")
        return None
    return res['result']

def dump_project(project_id):
    project = rpc_call("getProjectById", {"project_id": project_id})
    if not project: return None
    
    columns = rpc_call("getColumns", {"project_id": project_id})
    swimlanes = rpc_call("getAllSwimlanes", {"project_id": project_id})
    categories = rpc_call("getAllCategories", {"project_id": project_id})
    tasks = rpc_call("getAllTasks", {"project_id": project_id})
    
    return {
        "project": project,
        "columns": columns,
        "swimlanes": swimlanes,
        "categories": categories,
        "tasks": tasks
    }

data = {
    "71": dump_project(71),
    "72": dump_project(72)
}

with open('/tmp/projects_dump.json', 'w') as f:
    json.dump(data, f, indent=2)

print("Dumped 71 and 72 to /tmp/projects_dump.json")
