# Kanboard Python MCP Server & Automation Tools

This project provides a fully-featured **Model Context Protocol (MCP)** server for interacting with a Kanboard instance via its JSON-RPC API. It exposes Kanboard functionality directly to LLMs (like Claude, Antigravity, etc.).

Additionally, it contains a set of automation scripts for managing Kanboard projects (like swimlane management, AgileIndicators updates, and bulk task creation).

## Features

- **MCP Server (`kanboard_mcp_server.py`)**: A native MCP server exposing Kanboard tools.
  - **`get_project_master_map`**: Fetches a bird's eye view of a project, including active tasks and all attached Markdown (`.md`) files.
  - **`get_my_dashboard`**: Fetches a user's dashboard (all active projects, assigned tasks, unread notifications).
  - **Standard Task Tools**: `create_task`, `update_task`, `move_task_position`, `get_tasks`, etc.
- **Robust Error Handling**: Automatic fallback methods (e.g., trying `getAllProjectFiles` -> `getProjectFiles`) to handle different Kanboard versions or permission settings without crashing.
- **Diagnostic CLI Tools**: A built-in `--doctor` flag to verify network, credentials, and API connections before launching the server.
- **Swimlane & Column Management**: Reorder swimlanes, rename default lanes, and move tasks efficiently via Python scripts.
- **AgileIndicators Integration**: Apply Priority (P1-P5) and Complexity/Score (C0-C50) to your Kanboard tasks.

## Installation

1. Clone this repository.
2. Create a virtual environment: `python3 -m venv venv`
3. Activate it: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and fill in your Kanboard credentials. **(Never commit your `.env` file to version control!)**

## Usage

### Running the MCP Server
To use the server with an MCP client (like Antigravity or Claude Desktop):
```bash
python kanboard_mcp_server.py
```
*Note: MCP servers communicate over stdio, so you won't see terminal output directly unless you run with diagnostic flags.*

### Diagnostics
Check if your `.env` configuration and Kanboard API connection are working:
```bash
python kanboard_mcp_server.py --doctor
```

### Server Status
```bash
python kanboard_mcp_server.py --status
```

### Automation Scripts
Check the `scripts/` directory for ready-to-use Python scripts that automate common Kanboard workflows (e.g., bulk reordering, applying agile metrics).

### Kanboard MCP Araçları (Toplam: 21 Araç)

| Araç Adı | Kategori | Parametreler | Açıklama |
| :--- | :--- | :--- | :--- |
| `get_my_projects` | Proje Yönetimi | `` | Lists your own projects in Kanboard. |
| `get_project_by_id` | Proje Yönetimi | `project_id: int` | Gets the details of a single project. Returns an error for unauthorized projects. |
| `get_tasks_by_project` | Görev İşlemleri | `project_id: int` | Gets all tasks in the given project ID. |
| `get_task_details` | Görev İşlemleri | `task_id: int` | Gets all details of a specific task (title, description, assignee, category, date, etc.). |
| `get_user_tasks` | Görev İşlemleri | `` | Gets the overdue and open tasks of the current API user (or token owner). |
| `get_columns` | Proje Yönetimi | `project_id: int` | Lists the board columns in a project. Used to find IDs for moving tasks or creating tasks. |
| `create_task` | Görev İşlemleri | `project_id: int, title: str, description: str = "", column_id: int = 0, owner_id: int = 0, swimlane_id: int = 0` | Creates a new task. You can only create tasks in projects you are authorized for. |
| `update_task` | Görev İşlemleri | `task_id: int, title: str = "", description: str = "", owner_id: int = 0, category_id: int = 0, score: int = 0, swimlane_id: int = 0` | Updates an existing task. |
| `move_task_position` | Görev İşlemleri | `project_id: int, task_id: int, column_id: int, position: int = 1, swimlane_id: int = 0` | Moves a task to a specific column and position. |
| `create_comment` | Dosya & Yorumlar | `task_id: int, user_id: int, content: str` | Adds a comment to a specific task. |
| `get_all_subtasks` | Alt Görevler | `task_id: int` | Gets all subtasks for a given task. |
| `create_subtask` | Alt Görevler | `task_id: int, title: str, time_estimated: int = 0` | Creates a single subtask. |
| `create_bulk_subtasks` | Alt Görevler | `task_id: int, titles_csv: str` | Creates multiple subtasks from a comma-separated string of titles. |
| `get_all_swimlanes` | Proje Yönetimi | `project_id: int` | Lists all swimlanes for a project. |
| `change_swimlane_position` | Proje Yönetimi | `project_id: int, swimlane_id: int, position: int` | Changes the position of a swimlane. |
| `create_milestone` | Diğer | `project_id: int, title: str, column_id: int, date_str: str` | Creates a milestone task (colored yellow) for a specific date. |
| `schedule_waterfall` | Proje Yönetimi | `task_ids_csv: str, start_date_str: str, hours_per_subtask: int = 4` | Schedules a list of tasks sequentially (waterfall) starting from start_date_str. |
| `get_project_master_map` | Proje Yönetimi | `project_id: int` | Aggregates project metadata, active tasks, and project files into a single context map for Agent Swarm. |
| `create_external_task_link` | Bağımlılık & Harici Bağlantılar | `task_id: int, url: str, dependency: str, type: str = "weblink", title: str = ""` | Creates an external link for a task. |
| `create_task_link` | Bağımlılık & Harici Bağlantılar | `task_id: int, opposite_task_id: int, link_id: int` | Creates a link between two tasks. |
| `close_task` | Görev İşlemleri | `task_id: int` | Closes a task (sets is_active to 0). |

### SDLC Tarihçe Aktarıcısı (CLI)
```bash
python scripts/setup_project_tasks.py --project-id 7 --repo-path ~/dediaiproje/dedisoft/kanboard/plugins/ExecutiveDashboard --memory-dir docs/ai_chats/
```

*Not: `docs/ai_chats/` klasörü `.gitkeep` ile korunmaktadır ve içerisindeki yapay zeka chat logları (`.md`) izole bir şekilde saklanıp `git` tarafından yok sayılır (veya proje hafızası olarak Kanboard'a yüklenir).*
