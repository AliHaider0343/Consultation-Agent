import os
import streamlit as st
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import DeterministicFakeEmbedding
from uuid import uuid4
import nltk
from fireworks.client import Fireworks as client
from langchain_fireworks import FireworksEmbeddings

fireworks = client(api_key="fw_3ZYw86Am1N66XjT14X2nzvSH")

nltk.download('all', quiet=True)

# Configuration
CHROMA_DB_PATH = "chroma_db"
UPLOAD_PATH = "uploaded_files"
os.makedirs(CHROMA_DB_PATH, exist_ok=True)
os.makedirs(UPLOAD_PATH, exist_ok=True)

# Initialize Chroma vector store
embeddings = FireworksEmbeddings(
    model="nomic-ai/nomic-embed-text-v1.5",
)
vector_store = Chroma(
    collection_name="uploaded_files",
    embedding_function=embeddings,
    persist_directory=CHROMA_DB_PATH,
)

def get_documents_with_metadata(query, k=15):
    """
    Retrieve documents based on a search query and format them with XML-style tags and metadata.
    
    Args:
        query (str): The search query to find relevant documents
        k (int): Number of documents to retrieve (default: 5)
    
    Returns:
        str: Concatenated string of documents with XML-style tags and metadata
    """
    # Search for documents
    print("In docs Metadata")
    CHROMA_DB_PATH = "chroma_db"
    UPLOAD_PATH = "uploaded_files"
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)
    os.makedirs(UPLOAD_PATH, exist_ok=True)

# Initialize Chroma vector store
    embeddings = FireworksEmbeddings(
    model="nomic-ai/nomic-embed-text-v1.5",
)
    vector_store = Chroma(
    collection_name="uploaded_files",
    embedding_function=embeddings,
    persist_directory=CHROMA_DB_PATH,
)


    results = vector_store.similarity_search(query, k=k)
    
    # Format and concatenate results
    formatted_documents = []
    paths=set()
    for i, doc in enumerate(results, 1):
        # Create metadata dictionary
        metadata = {
            "doc_number": i,
            "file_name": doc.metadata.get('file_name', 'N/A'),
            "file_path": doc.metadata.get('file_path', 'N/A')
        }
        paths.add(metadata['file_path'])
        # Format document with XML-style tags
        formatted_doc = f'<doc meta={metadata}>\n{doc.page_content}\n</doc>'
        formatted_documents.append(formatted_doc)
    
    # Join all formatted documents with newlines
    final_output = "\n\n".join(formatted_documents)
    print("After metadata")
    return final_output,paths


def generate(query):
    context,paths=get_documents_with_metadata(query)
    print("context after")
    stream = fireworks.chat.completions.create(
        model="accounts/fireworks/models/llama-v3p1-8b-instruct",
        messages=[
            {
                "role": "system",
                "content": f"""
        You are an Expert Consulting Agent at Wychwood Partners with extensive knowledge in operational efficiency and the resources uploaded by Wychwood Partners.

        Response Instructions:
            Focus and User Query and then Respond.
            Just Answer the user QUestion directly doesnot opt any thing.
            Provide the Complete Response.
            Respond Only based on the Context.
            Provide clear, precise, and well-structured responses.
            Do not Return any answer out of your Context.
            Use Markdown elements such as headings, tables, bullet points, and other formatting tools to enhance readability and understanding.
            Offer detailed workflows, comprehensive explanations, and in-depth information from a variety of sources and references.
            Cover all relevant aspects of the given topic or question, incorporating perspectives from different resources within your knowledge.

        "Here are the relevant documents for the context:\n"

        <context>"{context}"</context>
              """,
            },
            {
                "role": "user",
                "content": query,
            },
        ],
        stream=True,
        temperature=0.0,
    )


    return {"response": stream,"paths":list(paths)}
