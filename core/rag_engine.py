import os
from langchain_mistralai import ChatMistralAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from core.vector_store import build_vector_store, load_vector_data, get_retriever


# Function to load the Mistral LLM
def get_llm():
    return ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.getenv("MISTRAL_API_KEY"),
        temperature=0.3
    )


# Function to format retrieved documents into plain text
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)


# Function to create the RAG prompt
def get_prompt():
    return ChatPromptTemplate.from_messages([
        (
            "system",
            """You are an expert meeting assistant. Answer the user's question based ONLY on the meeting transcript context provided below.
If User Question is related to Video and video transciption then you should answer that if question out of context then you can reply this is not given in video
If the answer is not found in the context, say:
"I could not find this information in the meeting transcript."

Always be concise and precise. If quoting someone, mention it clearly.

Context from meeting transcript:
{context}"""
        ),
        ("human", "{question}")
    ])


# Function to build a RAG chain from a new transcript
def build_rag_chain(transcript: str):
    vector_store = build_vector_store(transcript)
    retriever = get_retriever(vector_store, k=4)
    llm = get_llm()
    prompt = get_prompt()

    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


# Function to load an existing vector store and create a RAG chain
def load_rag_chain():
    vector_store = load_vector_data()
    retriever = get_retriever(vector_store, k=4)
    llm = get_llm()
    prompt = get_prompt()

    rag_chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain


# Function to ask a question and return the RAG answer
def ask_question(rag_chain, question: str) -> str:
    print(f"Question: {question}")

    answer = rag_chain.invoke(question)

    print(f"Answer: {answer}")

    return answer