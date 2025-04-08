# ragflow-mcp
Simple RAGFlow MCP. Only useful until the RAGFlow team releases the official MCP server

## Installation

We provide two installation methods. Method 2 (using uv) is recommended for faster installation and better dependency management.

### Method 1: Using conda

1. Create a new conda environment:

```bash
conda create -n ragflow_mcp python=3.12
conda activate ragflow_mcp
```

2. Clone the repository:

```bash
git clone https://github.com/oraichain/ragflow-mcp.git
cd ragflow-mcp
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

### Method 2: Using uv (Recommended)

1. Install uv (A fast Python package installer and resolver):

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone the repository:

```bash
git clone https://github.com/oraichain/ragflow-mcp.git
cd ragflow-mcp
```

3. Create a new virtual environment and activate it:

```bash
uv venv --python 3.12
source .venv/bin/activate  # On Unix/macOS
# Or on Windows:
# .venv\Scripts\activate
```

4. Install dependencies:

```bash
uv pip install -r pyproject.toml
```

# Run MCP Server Inspector for debugging

1. Start the MCP server

2. Start the inspector using the following command:

```bash
# you can choose a different server
SERVER_PORT=9000 npx @modelcontextprotocol/inspector