import os
import sys
import datetime

# Add parent directory to path to import kanboard_mcp_server
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from kanboard_mcp_server import kanboard_call

def fetch_column_id_by_name(project_id, column_name):
    """Helper to fetch a column ID by its name."""
    cols = kanboard_call('getColumns', {"project_id": project_id})
    if not cols:
        return None
    for c in cols:
        if c['title'].lower() == column_name.lower():
            return c['id']
    return cols[0]['id']  # Fallback to first column

def create_roadmap_tasks(project_id, column_name="Bekleme listesi"):
    """
    Creates multiple roadmap tasks in a specific column.
    (Example function based on the Enterprise Roadmap)
    """
    col_id = fetch_column_id_by_name(project_id, column_name)
    
    tasks = [
        {
            "title": "A. Veri İçe Aktarma Motoru",
            "description": "Personel, stok vb. verileri CSV/XLS ile aktarma özelliği.",
            "column_id": col_id
        },
        {
            "title": "B. Taşeron Yönetimi",
            "description": "Alt kiracı ve taşeron ilişkisinin kurulması.",
            "column_id": col_id
        }
    ]
    
    print(f"Creating roadmap tasks in project {project_id}...")
    for t in tasks:
        t["project_id"] = project_id
        res = kanboard_call('createTask', t)
        print(f"Created task: {t['title']} -> Task ID: {res}")

def add_subtasks_to_task(task_id, subtask_titles):
    """Adds a list of subtasks to a specific task."""
    print(f"Adding subtasks to Task {task_id}...")
    for title in subtask_titles:
        kanboard_call('createSubtask', {"task_id": task_id, "title": title})
        print(f" - Added subtask: {title}")

def schedule_waterfall(task_ids, start_date_str, hours_per_subtask=4):
    """
    Calculates estimated time based on subtasks and schedules tasks 
    sequentially starting from a specific date.
    """
    current_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
    
    print("Scheduling waterfall dates for tasks...")
    for t_id in task_ids:
        subtasks = kanboard_call('getAllSubtasks', {"task_id": t_id})
        
        num_subtasks = len(subtasks) if subtasks else 1
        total_hours = num_subtasks * hours_per_subtask
        days_needed = num_subtasks
        
        start_date_fmt = current_date.strftime("%Y-%m-%d")
        end_date = current_date + datetime.timedelta(days=max(days_needed - 1, 0))
        due_date_fmt = end_date.strftime("%Y-%m-%d")
        
        # Assign estimated time to subtasks
        if subtasks:
            for st in subtasks:
                kanboard_call('updateSubtask', {
                    "id": st["id"],
                    "task_id": t_id,
                    "time_estimated": hours_per_subtask
                })
                
        # Update parent task dates and total estimated time
        kanboard_call('updateTask', {
            "id": t_id,
            "date_started": start_date_fmt,
            "date_due": due_date_fmt,
            "time_estimated": total_hours
        })
        
        print(f"Task {t_id} scheduled: {start_date_fmt} to {due_date_fmt} (Total: {total_hours}h)")
        current_date = end_date + datetime.timedelta(days=1)

def create_milestone(project_id, column_name, title, date_str):
    """Creates a highlighted milestone task."""
    col_id = fetch_column_id_by_name(project_id, column_name)
    
    t = {
        "project_id": project_id,
        "title": f"🚩 KİLOMETRE TAŞI: {title}",
        "description": "Bu bir milestone (hedef) görevidir.",
        "column_id": col_id,
        "date_started": date_str,
        "date_due": date_str,
        "color_id": "yellow"  # Highlight color
    }
    res = kanboard_call('createTask', t)
    print(f"Created milestone: {title} -> Task ID: {res}")

if __name__ == '__main__':
    print("Kanboard Automations Example Script")
    print("Usage: Import these functions in your custom scripts to automate Kanboard workflows.")
    # Example usage:
    # create_roadmap_tasks(project_id=72)
    # schedule_waterfall(task_ids=[101, 102], start_date_str="2026-08-20")
