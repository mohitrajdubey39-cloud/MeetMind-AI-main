from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os

def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.2
    )

def build_chain(system_prompt: str):
    llm = get_llm()

    return (
        ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{text}"),
        ])
        | llm
        | StrOutputParser()
    )

def extract_action_items(transcript: str) -> str:
    chain = build_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all action items. For each provide:\n"
        "- Task description\n"
        "- Owner (who is responsible)\n"
        "- Deadline (if mentioned, otherwise write 'Not specified')\n\n"
        "Format as a numbered list. "
        "If none are found, say 'No action items found.'"
    )

    return chain.invoke({"text": transcript})

def extract_key_decisions(transcript: str) -> str:
    chain = build_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all key decisions that were actually made. "
        "Do not include suggestions or discussions that were not finalized.\n\n"
        "Format as a numbered list. "
        "If none are found, say 'No key decisions found.'"
    )

    return chain.invoke({"text": transcript})

def extract_questions(transcript: str) -> str:
    chain = build_chain(
        "You are an expert meeting analyst. From the meeting transcript, "
        "extract all unresolved questions, pending issues, "
        "or topics requiring follow-up.\n\n"
        "Format as a numbered list. "
        "If none are found, say 'No open questions found.'"
    )

    return chain.invoke({"text": transcript})