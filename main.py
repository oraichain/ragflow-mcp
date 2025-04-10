from starlette.applications import Starlette
from starlette.requests import Request

from starlette.routing import Mount, Host, Route
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.sse import SseServerTransport
from starlette.types import Receive, Scope, Send
from auth import JwtAuthTransport
import uvicorn
import os
from dotenv import load_dotenv
from configs.ragflow import ragflow
from services.chat_assistant import ask_ragflow, create_chat_session
from services.dataset import create_initial_dataset, get_dataset_by_name
from settings import settings
import json
from global_session import user_sessions
import asyncio

load_dotenv()


def get_transport():
    try:
        if settings.enable_auth:
            return JwtAuthTransport("/messages/")
        return SseServerTransport("/messages/")
    except Exception as e:
        print(f"Warning: Error initializing transport: {e}")
        return SseServerTransport("/messages/")  # Fallback to SSE transport


mcp = FastMCP("Ragflow MCP")
transport = get_transport()


async def handle_sse(request):
    try:
        async with transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await mcp._mcp_server.run(
                streams[0],
                streams[1],
                mcp._mcp_server.create_initialization_options(),
            )
    except Exception as e:
        print(f"Error in handle_sse: {e}")
        raise


async def wrap_handle_post_message(scope: Scope,
                                   receive: Receive,
                                   send: Send):
    temp_request = Request(scope, receive)
    authorization = temp_request.headers.get("authorization")
    # ---- Start modify body ----
    original_body_bytes = b''
    original_receive = receive
    more_body = True
    while more_body:
        message = await original_receive()
        print(f"Received message: {message}")
        if message['type'] == 'http.request':
            original_body_bytes += message.get('body', b'')
            more_body = message.get('more_body', False)
        elif message['type'] == 'http.disconnect':
            print("Client disconnected while reading body")
            return
        else:
            pass

    modified_body_bytes = original_body_bytes
    try:
        # Parse JSON
        data = json.loads(original_body_bytes.decode('utf-8'))
        if 'params' in data and 'arguments' in data['params']:
            if settings.enable_auth:
                data['params']['arguments']['dataset_name'] = authorization
        modified_body_bytes = json.dumps(data).encode('utf-8')
    except json.JSONDecodeError as e:
        print(f"Warning: Could not parse request body as JSON: {e}")

    except Exception as e:
        print(f"Error during body modification: {e}")
    _receive_called = False

    async def modified_receive():
        nonlocal _receive_called
        if not _receive_called:
            _receive_called = True
            return {'type': 'http.request', 'body': modified_body_bytes, 'more_body': False}
        else:
            await asyncio.sleep(3600)
            return {'type': 'http.disconnect'}

    return await transport.handle_post_message(scope, modified_receive, send)

app = Starlette(
    routes=[
        Route('/sse/', endpoint=handle_sse),
        Mount("/messages/", app=wrap_handle_post_message)
    ]
)


@mcp.tool()
def get_ragflow_datasets() -> str:
    try:
        datasets = ragflow.list_datasets()
        return datasets
    except Exception as e:
        return f"Error fetching datasets: {str(e)}"


@mcp.tool()
def create_rag(name: str) -> str:
    """Creates a initial knowledge base and dataset for the user.

    Args:
        name (str): The name of the dataset to create,

    Returns:
        str: Response from the API indicating success or failure
    """
    existed_datasets = get_dataset_by_name(name)
    if len(existed_datasets) > 0:
        return f"Dataset '{name}' already exists"
    try:
        response = create_initial_dataset(name)
        return f"Successfully created dataset '{name}': {response.id}"
    except Exception as e:
        return f"Failed to create dataset: {str(e)}"


@mcp.tool()
def upload_rag(dataset_name: str, display_names: list[str], blobs: list[str]) -> str:
    """Uploads documents and provide more knowledge base for the dataset.

    Args:
        dataset_name (str): The name of the dataset to upload documents to
        display_names (list[str]): List of display names for the documents
        blobs (list[str]): List of document contents as strings

    Returns:
        str: Response from the API indicating success or failure
    """
    try:
        print("dataset_name", dataset_name)
        dataset = ragflow.get_dataset(name=dataset_name)

        documents = []
        for display_name, blob in zip(display_names, blobs):
            documents.append({
                "display_name": display_name,
                "blob": blob
            })

        # Upload documents
        response = dataset.upload_documents(documents)

        # Get document IDs
        doc_info = []
        for doc in response:
            dataset.async_parse_documents([doc.id])
            doc_info.append({
                "name": doc.display_name if hasattr(doc, 'display_name') else display_names[0],
                "id": doc.id
            })

        # training

        return {
            "status": "success",
            "message": f"Successfully uploaded {len(documents)} documents",
            "dataset": dataset_name,
            "documents": doc_info
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@mcp.tool()
def query_rag(dataset_name: str, query: str) -> str:
    """
    Queries the specified dataset in the knowledge base to retrieve an answer based on the provided query.

    Args:
        dataset_name (str): The name of the dataset to query.
        query (str): The question or query string to search for in the dataset.

    Returns:
        str: A dictionary containing:
            - "reference": Details of the reference data from the knowledge base, including content and source information.
            - "answer": The answer derived from the knowledge base. If the answer is not found, a message indicating this will be returned.

    Raises:
        Exception: If an error occurs during the query process, an error message is returned.
    """
    try:
        response = ask_ragflow(dataset_name, query)
        return {
            "reference": response['data']['reference'],
            "answer": response['data']['answer']
        }
    
    except Exception as e:
        return f"Error querying dataset: {str(e)}"


# or dynamically mount as host
app.router.routes.append(Host('mcp.acme.corp', app=app))

if __name__ == "__main__":
    # Run the server with Uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
