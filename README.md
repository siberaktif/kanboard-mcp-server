==============================
Python API Client for Kanboard
==============================

Client library for Kanboard API.

- Author: Frédéric Guillot
- License: MIT

Installation
============

.. code-block:: bash

    python3 -m pip install kanboard


- This library is compatible with Python >= 3.9.

On Fedora (36 and later), you can install the package using DNF:

.. code-block:: bash

    dnf install python3-kanboard


Examples
========

Methods and arguments are the same as the JSON-RPC procedures described in the
`official documentation <https://docs.kanboard.org/v1/api/>`_.

Python methods are dynamically mapped to the API procedures: **You must use named arguments**.

By default, calls are made synchronously, meaning that they will block the program until completed.

Creating a new team project
---------------------------

.. code-block:: python

    import kanboard

    with kanboard.Client("http://localhost/jsonrpc.php", "jsonrpc", "your_api_token") as kb:
        project_id = kb.create_project(name="My project")


Authenticate as user
--------------------

.. code-block:: python

    import kanboard

    with kanboard.Client("http://localhost/jsonrpc.php", "admin", "secret") as kb:
        kb.get_my_projects()

Use a custom authentication header
-----------------------------------

If your Kanboard instance uses a custom authentication header
(for example, ``define('API_AUTHENTICATION_HEADER', 'X-My-Custom-Auth-Header');``
in your Kanboard configuration):

.. code-block:: python

    import kanboard

    with kanboard.Client(url="http://localhost/jsonrpc.php",
                         username="demo",
                         password="secret",
                         auth_header="X-My-Custom-Auth-Header") as kb:
        kb.get_me()

Create a new task
-----------------

.. code-block:: python

    import kanboard

    with kanboard.Client("http://localhost/jsonrpc.php", "jsonrpc", "your_api_token") as kb:
        project_id = kb.create_project(name="My project")
        task_id = kb.create_task(project_id=project_id, title="My task title")

Use a personalized user agent
-----------------------------

.. code-block:: python

    import kanboard

    with kanboard.Client(url="http://localhost/jsonrpc.php",
                         username="admin",
                         password="secret",
                         user_agent="My Kanboard client") as kb:
        kb.get_my_projects()

Request timeout
---------------

By default, requests time out after 30 seconds. You can change this with the
``timeout`` parameter (in seconds), or set it to ``None`` to disable the timeout:

.. code-block:: python

    import kanboard

    # Custom 60-second timeout
    with kanboard.Client(url="http://localhost/jsonrpc.php",
                         username="admin",
                         password="secret",
                         timeout=60) as kb:
        kb.get_my_projects()

Error handling
--------------

The client raises ``kanboard.ClientError`` for API errors, network failures,
and malformed responses:

.. code-block:: python

    import kanboard

    with kanboard.Client("http://localhost/jsonrpc.php", "jsonrpc", "your_api_token") as kb:
        try:
            kb.create_project(name="My project")
        except kanboard.ClientError as e:
            print(e)

SSL connection and self-signed certificates
===========================================

Example with a valid certificate:

.. code-block:: python

    import kanboard

    with kanboard.Client("https://example.org/jsonrpc.php", "admin", "secret") as kb:
        kb.get_my_projects()

Example with a custom certificate:

.. code-block:: python

    import kanboard

    with kanboard.Client(url="https://example.org/jsonrpc.php",
                         username="admin",
                         password="secret",
                         cafile="/path/to/my/cert.pem") as kb:
        kb.get_my_projects()

Example with a custom certificate and hostname mismatch:

.. code-block:: python

    import kanboard

    with kanboard.Client(url="https://example.org/jsonrpc.php",
                         username="admin",
                         password="secret",
                         cafile="/path/to/my/cert.pem",
                         ignore_hostname_verification=True) as kb:
        kb.get_my_projects()

.. warning::

    Setting ``insecure=True`` disables all certificate validation and hostname
    checks, making your application vulnerable to man-in-the-middle (MitM) attacks:

.. code-block:: python

    import kanboard

    with kanboard.Client(url="https://example.org/jsonrpc.php",
                         username="admin",
                         password="secret",
                         insecure=True) as kb:
        kb.get_my_projects()

Asynchronous I/O
================

The client also exposes async/await style method calls. Similarly to the synchronous calls (see above),
the method names are mapped to the API methods.

To invoke an asynchronous call, the method name must be appended with ``_async``. For example, a synchronous call
to ``create_project`` can be made asynchronous by calling ``create_project_async`` instead.

.. code-block:: python

    import asyncio
    import kanboard

    async def main():
        with kanboard.Client("http://localhost/jsonrpc.php", "jsonrpc", "your_api_token") as kb:
            project_id = await kb.create_project_async(name="My project")
            print(project_id)

    asyncio.run(main())


See the `official API documentation <https://docs.kanboard.org/v1/api/>`_ for the complete list of
methods and arguments.

MCP Server
==========

This project also includes an MCP (Model Context Protocol) Server for Kanboard. The server exposes Kanboard API methods to LLMs acting as MCP clients.

Installation and Running (Kurulum ve Çalıştırma)
------------------------------------------------
This server requires **Python 3.10+**.

Running the Server / Sunucuyu Çalıştırma
----------------------------------------
Ensure you have installed the required dependencies from ``requirements.txt``:

.. code-block:: bash

    pip install -r requirements.txt

You can run and test the server in development mode using the MCP CLI:

.. code-block:: bash

    mcp dev kanboard_mcp_server.py

Command Line Options (Komut Satırı Seçenekleri)
-----------------------------------------------
The server script includes helpful built-in commands for debugging and status checks:

.. code-block:: bash

    # Show help message / Yardım mesajını gösterir
    python kanboard_mcp_server.py --help

    # Show server status / Sunucu durumunu gösterir
    python kanboard_mcp_server.py --status

    # Run diagnostics (checks .env and tests connection to Kanboard)
    # Teşhis araçlarını çalıştırır (.env kontrolü, bağlantı testi)
    python kanboard_mcp_server.py --doctor

*(When run without any arguments, the script will output a startup message to `stderr` and begin listening on `stdio` for MCP protocol messages. / Argümansız çalıştırıldığında sunucu MCP protokolü için dinlemeye başlar.)*

Configuration (Yapılandırma)
----------------------------
Create a `.env` file in the root directory based on `.env.example`. **Never commit your `.env` file to version control.** Always use `.env.example` as a template for others.

.. code-block:: bash

    cp .env.example .env

Variables in `.env`:

- ``KANBOARD_URL``: The JSON-RPC endpoint (e.g. ``https://dedikanban.dedimetri.com/jsonrpc.php``)
- ``KANBOARD_USERMAIL`` or ``KANBOARD_USERNAME``: Your user email or username
- ``KANBOARD_PASSWORD``: Your Kanboard password
- ``KANBOARD_API_TOKEN``: Your personal or system API token (takes precedence over password)

MCP Client Integration Guide (MCP İstemcisi Entegrasyon Rehberi)
----------------------------------------------------------------
The MCP server uses standard Input/Output (`stdio`) for communication. You can connect various AI clients to this server by configuring them to spawn this script.

An example configuration file is provided in ``mcp.json.example``.

**Standard Configuration Example (`mcp.json` / `claude_desktop_config.json`):**

.. code-block:: json

    {
      "mcpServers": {
        "kanboard": {
          "command": "python",
          "args": ["/path/to/kanboard_mcp_server.py"],
          "env": {
            "KANBOARD_URL": "https://www.dedikanban.dedimetri.com/jsonrpc.php",
            "KANBOARD_USERMAIL": "kullanici@example.com",
            "KANBOARD_API_TOKEN": "token_buraya"
          }
        }
      }
    }

**Platform Specific Integration Instructions:**

- **Claude Desktop:** Open your Claude Desktop settings, click on Developer -> Edit Config, and paste the configuration above into `claude_desktop_config.json`. Ensure the `args` path points to the absolute path of `kanboard_mcp_server.py`. Restart Claude Desktop. (Linux and Windows paths must be correctly formatted).
- **Antigravity CLI & Hermes CLI:** Drop the `mcp.json` file into the appropriate configuration directory of the CLI or pass it via the `--mcp` flag depending on the documentation.
- **VS Code (Copilot / Cline / Roo Code):** In your MCP settings for these extensions, add a new server using `stdio` transport. Provide `python` as the command and the absolute path to `kanboard_mcp_server.py` as the argument. Add the environment variables identically to the JSON above.
- **OpenAI / ChatGPT:** Currently, ChatGPT supports custom GPT actions via OpenAPI specs, not direct MCP `stdio`. However, wrappers or local proxy tools can bridge MCP to a REST endpoint if needed.

Publishing to GitHub / Git (GitHub'a Yükleme Adımları)
------------------------------------------------------
To upload this project to a new Git repository (e.g., GitHub or Forgejo), run:

.. code-block:: bash

    git init
    git branch -m main
    git add .
    git commit -m "Initial commit for Kanboard MCP Server"
    git remote add origin <YOUR_REPOSITORY_URL>
    git push -u origin main

*(Make sure your `.gitignore` includes `.env` so you do not accidentally expose your API tokens!)*

Credits and License (Kredi ve Lisans)
-------------------------------------
This project was built utilizing the following resources:
- Kanboard API Reference: https://docs.kanboard.org/v1/api/
- Base Kanboard Python Client: https://github.com/kanboard/python-api-client

This project is licensed under the **MIT License**.

