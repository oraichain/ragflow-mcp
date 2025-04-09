from configs.ragflow import ragflow
from ragflow_sdk import Chat
from settings import settings

llm_chat = Chat.LLM(
    model_name=settings.model_name) if settings.model_name else None


def create_chat_assistant(user_id: str):
    datasets = ragflow.list_datasets(name=user_id)
    dataset_ids = []
    for dataset in datasets:
        dataset_ids.append(dataset.id)
    return ragflow.create_chat(user_id, dataset_ids=dataset_ids, llm=llm_chat)


def get_chat_assistant(user_id: str):
    chat = ragflow.get_chat(user_id)
