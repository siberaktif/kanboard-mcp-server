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
