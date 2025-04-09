import json
import logging
from configs.ragflow import ragflow
from ragflow_sdk import Chat
from settings import settings
from configs.logger import get_logger

logger = get_logger(__name__)

llm_chat = Chat.LLM({
    "model_name": settings.model_name
}, {}) if settings.model_name else None


def get_dataset_by_name(user_id: str):
    try:
        datasets = ragflow.list_datasets(name=user_id)
        return datasets
    except Exception as e:
        logger.error(f"Error getting dataset by name {user_id}: {e}")
        return []


def create_dummy_dataset(user_id: str):
    existed_datas = get_dataset_by_name(user_id)
    if len(existed_datas) > 0:
        return existed_datas[0]
    dataset = ragflow.create_dataset(name=user_id)
    dataset.upload_documents([{
        "display_name": "base_knowledge.txt",
        "blob": json.dumps({
            "text": "You are a helpful assistant that can answer questions about the user's data."
        })
    }])
    return dataset


def create_chat_assistant(user_id: str):
    datasets = get_dataset_by_name(user_id)
    dataset_ids = [dataset.id for dataset in datasets]
    return ragflow.create_chat(user_id, dataset_ids=dataset_ids, llm=llm_chat)


def get_chat_assistant(user_id: str):
    chats = []
    try:
        chats = ragflow.list_chats(name=user_id)
    except Exception as e:
        chats = []
    if len(chats) > 0:
        datasets = get_dataset_by_name(user_id)
        dataset_ids = [dataset.id for dataset in datasets]
        chat = chats[0]
        chat.update({"dataset_ids": dataset_ids})
        return chat
    else:
        return create_chat_assistant(user_id)


def create_chat_session(user_id: str, session_name: str = "New session"):
    chat = get_chat_assistant(user_id)
    if not chat:
        return None
    return chat.create_session(session_name)


def get_chat_session(user_id: str, params: dict = {}):
    chat = get_chat_assistant(user_id)
    return chat.list_sessions(**params)


# test
if __name__ == "__main__":
    user_id = "new_user_id"
    dataset = create_dummy_dataset(user_id)
    assistant = get_chat_assistant(user_id)
    newSession = create_chat_session(user_id)
    print("New session created: ", newSession)
    sessions = get_chat_session(user_id)
    print("Sessions: ", sessions)
