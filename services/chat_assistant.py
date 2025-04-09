from datetime import datetime
from configs.ragflow import ragflow
from ragflow_sdk import Chat
from services.dataset import create_initial_dataset, get_dataset_by_name
from settings import settings
from configs.logger import get_logger
import requests
import json

logger = get_logger(__name__)

llm_chat = Chat.LLM({}, {"model_name": settings.model_name}
                    ) if settings.model_name else None


def create_chat_assistant(user_id: str):
    datasets = get_dataset_by_name(user_id)
    if len(datasets) == 0:
        datasets = [create_initial_dataset(user_id)]
    dataset_ids = [dataset.id for dataset in datasets]
    return ragflow.create_chat(user_id, dataset_ids=dataset_ids, llm=llm_chat)


def get_chat_assistant(user_id: str):
    chats = []
    try:
        chats = ragflow.list_chats(name=user_id)
    except Exception as e:
        chats = []
    if len(chats) > 0:
        return chats[0]
    else:
        return create_chat_assistant(user_id)


def create_chat_session(user_id: str):
    chat = get_chat_assistant(user_id)
    if not chat:
        return None
    session_name = f"New session {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    return chat.create_session(session_name)


def get_chat_session(user_id: str):
    sessions = []
    try:
        chat = get_chat_assistant(user_id)
        sessions = chat.list_sessions()
    except Exception as e:
        logger.error(f"Error getting chat session: {e}")
        return []
    if len(sessions) > 0:
        return sessions[0]
    else:
        return create_chat_session(user_id)


def ask_ragflow(user_id: str, question: str, stream: bool = False):
    session = create_chat_session(user_id)
    if not session:
        return None

    url = f"{settings.ragflow_base_url}/api/v1/chats/{session.chat_id}/completions"

    payload = json.dumps({
        "question": question,
        "stream": stream,
        "session_id": session.id
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {settings.ragflow_api_key}'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()
# test
# if __name__ == "__main__":
#     user_id = "new_user_id"
#     dataset = create_dummy_dataset(user_id)
#     assistant = get_chat_assistant(user_id)
#     newSession = create_chat_session(user_id)
#     print("New session created: ", newSession)
#     sessions = get_chat_session(user_id)
#     print("Sessions: ", sessions)
