from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.runnables import RunnablePassthrough , RunnableLambda

import os

# Load LLM

def get_llm():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise RuntimeError("MISTERAL_API_KEY is not set in environment / .env")

    return ChatMistralAI(
        model="mistral-small-latest",
        api_key=api_key,
        temperature=0.3
    )

#Split trans

def split_transcription(transcription: str) -> list:
    """Splits the transcription into smaller chunks."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=300,
    )
    return text_splitter.split_text(transcription)


# summary of trans
def summarize_transcription(transcription: str) -> str:
    """Summarizes the transcription using Mistral AI."""
    llm = get_llm()

    map_prompt = ChatPromptTemplate.from_messages(
        [
        ("system", "Summarize this portion of a meeting transcript concisely."),
        ("human", "{text}"),
        ]
    )

    map_chain =  map_prompt | llm | StrOutputParser()

    chunks  =  split_transcription(transcription)

    chunk_summary = [map_chain.invoke(
        {
            "text" : chunk
        }
    )
    for chunk in chunks
    ]

    combined = "\n\n".join(chunk_summary)

    combined_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert meeting summarizer. Combine these partial summaries "
                "into one final professional meeting summary in bullet points.",
            ),
            ("human", "{text}"),
        ]
    )

    combined_chain = combined_prompt | llm | StrOutputParser()

    return combined_chain.invoke({"text": combined})



def generate_title(transcipt : str) -> str:
    llm = get_llm()

    title_chain = (
        RunnablePassthrough() | RunnableLambda(lambda x:{"text":x}) | 
        ChatPromptTemplate.from_messages([
             (
                "system",
                "Based on the meeting transcript, generate a short professional meeting title "
                "(max 8 words). Only return the title, nothing else.",
            ),
            ("human", "{text}"),
        ])
        | llm
        |StrOutputParser()
    )

    return title_chain.invoke(transcipt[:2000])